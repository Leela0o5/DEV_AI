import argparse
import sys
from orchestrator import run_orchestrator

def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Pipeline - Orchestrator-Worker Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Research Python async patterns and write example code"
  python main.py "Analyze the performance of sorting algorithms"
  python main.py --interactive
        """
    )
    
    parser.add_argument(
        "task",
        nargs="?",
        help="Task to execute (required unless --interactive)"
    )
    
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Enter interactive mode for multi-turn conversations"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.task:
        result = run_orchestrator(args.task)
        print("\n" + "="*80)
        print("FINAL RESULT")
        print("="*80 + "\n")
        print(result)
    else:
        parser.print_help()
        sys.exit(1)

def interactive_mode():
    """Interactive mode for multi-turn conversations."""
    print("Multi-Agent Pipeline - Interactive Mode")
    print("Type 'exit' or 'quit' to exit\n")
    
    while True:
        try:
            task = input("\n> Task: ").strip()
            
            if task.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            
            if not task:
                continue
            
            print("\nProcessing...")
            result = run_orchestrator(task)
            print("\n" + "="*80)
            print("RESULT")
            print("="*80 + "\n")
            print(result)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue

if __name__ == "__main__":
    main()
