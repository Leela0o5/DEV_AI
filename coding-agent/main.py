import argparse
from dotenv import load_dotenv
from src.agent import run_agent_loop

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Autonomous Coding Agent CLI",
        epilog='''Examples:
  python main.py "Fix the math_utils.py file to pass the test_math.py tests"
  python main.py "Write a simple linked list implementation in linked_list.py along with tests"'''
    )
    
    parser.add_argument(
        "task_prompt",
        type=str,
        help="The instruction or task to give to the coding agent."
    )

    args = parser.parse_args()
    run_agent_loop(args.task_prompt)

if __name__ == "__main__":
    main()
