from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.panel import Panel

from src.actions import print_summary_table, run_action_loop
from src.agent import categorize_emails
from src.gmail import authenticate, fetch_emails

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="email-agent",
        description="A Gmail agent that reads, categorizes, and acts on your inbox.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py                  # process last 20 emails interactively\n"
            "  python main.py --max 10         # process last 10 emails\n"
            "  python main.py --dry-run        # categorize only, no actions\n"
            "  python main.py --auto-archive   # auto-archive newsletters, confirm everything else\n"
        ),
    )
    parser.add_argument("--max", type=int, default=20, metavar="N",
                        help="Number of recent emails to fetch (default: 20)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Categorize and show proposed actions, but execute nothing")
    parser.add_argument("--auto-archive", action="store_true",
                        help="Automatically archive newsletters without confirmation")
    args = parser.parse_args()

    console.print()
    console.print(Panel.fit("[bold]Email Agent[/bold]", border_style="cyan"))

    if args.dry_run:
        console.print("  [dim]Dry-run mode — no changes will be made.[/dim]\n")

    #  Authenticate and fetch
    with console.status("  Connecting to Gmail...", spinner="dots"):
        try:
            service = authenticate()
        except FileNotFoundError as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}")
            sys.exit(1)

    with console.status(f"  Fetching {args.max} emails...", spinner="dots"):
        emails = fetch_emails(service, max_results=args.max)

    if not emails:
        console.print("  [dim]No emails found in inbox.[/dim]")
        return

    console.print(f"  Fetched [bold]{len(emails)}[/bold] emails.\n")

    #  Categorize with Gemini
    with console.status("  Categorizing with Gemini...", spinner="dots"):
        analyses = categorize_emails(emails)

    # Show summary table
    print_summary_table(emails, analyses)

    if args.dry_run:
        console.print("\n  [dim]Dry-run complete. Use without --dry-run to take actions.[/dim]\n")
        # Still offer the action loop but it will never execute writes
        run_action_loop(service, emails, analyses, dry_run=True, auto_archive=False)
        return

    #  Human-in-the-loop action loop
    console.print("\n  [bold]Starting action loop — press Enter to skip any action.[/bold]\n")
    run_action_loop(
        service, emails, analyses,
        dry_run=False,
        auto_archive=args.auto_archive,
    )

    console.print()
    console.print(Panel.fit("[bold green]Done.[/bold green]", border_style="green"))
    console.print()


if __name__ == "__main__":
    main()
