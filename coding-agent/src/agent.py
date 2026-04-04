import os
from google import genai
from google.genai import types

from src.tools import list_files, read_file, write_file, run_tests, task_complete

# Maximum loops before the agent bails out (Circuit Breaker)
MAX_ATTEMPTS = 15

SYSTEM_PROMPT = """You are an autonomous senior software engineer and coding agent. 
Your ONLY purpose is to write, execute, observe, and fix code based on the user's instructions.
If a user prompt is completely unrelated to programming, creating files, or modifying the workspace, you must politely decline and state your purpose.

You operate in a strict "Write -> Execute -> Observe -> Fix" loop.
1. Use `list_files` to understand the workspace structure.
2. Use `read_file` to read the buggy Python and Test files.
3. Use `write_file` to create or modify code.
4. Use `run_tests` to execute pytest on the workspace and observe the output.
5. If the tests FAIL, carefully read the traceback, use `write_file` to fix the code, and run `run_tests` again.
6. When tests PASS (Exit code 0), call `task_complete`.

You do not need human intervention. Keep fixing errors until you succeed.
Always run tests to verify your changes!
"""

def run_agent_loop(user_task: str):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        return

    client = genai.Client()

    # We provide our custom functions to the model
    tools = [list_files, read_file, write_file, run_tests, task_complete]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=tools,
        temperature=0.2, # Low temperature for more deterministic coding behavior
    )

    print(f"Agent started with task:\n'{user_task}'\n")

    # Start the chat session
    chat = client.chats.create(
        model="gemini-flash-latest",
        config=config
    )

    # First message is the user's CLI prompt
    message_to_send = user_task

    attempts = 0
    while attempts < MAX_ATTEMPTS:
        attempts += 1
        print(f"\n--- [Iteration {attempts}/{MAX_ATTEMPTS}] ---")
        
        try:
            response = chat.send_message(message_to_send)
        except Exception as e:
            print(f"Error communicating with Gemini: {e}")
            break

        # Check if the model called any tools
        if response.function_calls:
            # We must process all function calls in this turn and return the results
            tool_responses = []
            
            for call in response.function_calls:
                func_name = call.name
                args = call.args or {}
                
                print(f"Agent called tool: {func_name}({args})")
                
                # Execute the matched local function
                result_str = ""
                if func_name == "list_files":
                    result = list_files(**args)
                    result_str = "\n".join(result) if result else "No files found."
                elif func_name == "read_file":
                    result_str = read_file(**args)
                elif func_name == "write_file":
                    result_str = write_file(**args)
                elif func_name == "run_tests":
                    result_str = run_tests()
                    print(f"   -> Test Run returned:\n{result_str[:300]}...\n")
                elif func_name == "task_complete":
                     print(" Agent declared the task complete!")
                     return
                else:
                    result_str = f"Error: Unknown tool '{func_name}'"
                
                # Package the result back to continue the loop
                tool_responses.append(types.Part.from_function_response(
                    name=func_name,
                    response={"result": result_str}
                ))
            
            # The next message we send back is just the raw tool responses.
            message_to_send = tool_responses
            
        else:
            # The agent spoke directly instead of using a tool
            print(f"Agent says: {response.text}")
            
            message_to_send = "Please continue using your tools to solve the task, run tests, or call `task_complete` if you are finished."

    if attempts >= MAX_ATTEMPTS:
        print("Circuit Breaker triggered! Max attempts reached. Agent stopping to prevent infinite loop.")
