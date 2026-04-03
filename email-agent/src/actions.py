""" Human-in-the-loop confirmation and action execution."""

from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from src.agent import draft_reply
from src.gmail import apply_label, archive_message, send_reply

console = Console()

CATEGORY_COLORS = {
    "urgent": "bold red",
    "action_required": "bold yellow",
    "fyi": "dim",
    "newsletter": "blue",
}


def confirm(prompt: str) -> bool:
    """Ask y/n. Defaults to no — safe by default."""
    answer = Prompt.ask(f"  {prompt} [y/N]", default="n")
    return answer.strip().lower() == "y"


def present_email(email: dict, analysis: dict) -> None:
    """Display a rich panel with email details and Gemini's analysis."""
    cat = analysis.get("category", "fyi")
    color = CATEGORY_COLORS.get(cat, "white")
    priority = analysis.get("priority", 5)
    summary = analysis.get("summary", "")

    header = Text()
    header.append(f"[{cat.upper()}]  ", style=color)
    header.append(f"Priority {priority}/10  ", style="bold")
    header.append(summary, style="italic")

    body = (
        f"[bold]From:[/bold]    {email['sender']}\n"
        f"[bold]Date:[/bold]    {email['date']}\n"
        f"[bold]Subject:[/bold] {email['subject']}\n\n"
        f"[dim]{email['snippet']}[/dim]"
    )

    console.print()
    console.print(Panel(body, title=header, border_style=color.replace("bold ", ""), expand=False))


def _handle_reply(service, email: dict, dry_run: bool) -> None:
    """Draft a reply, show it, and optionally send after confirmation."""
    with console.status("  Drafting reply...", spinner="dots"):
        draft = draft_reply(email)

    console.print(Panel(draft, title="[bold]Proposed Reply[/bold]", border_style="cyan", padding=(1, 2)))

    if dry_run:
        console.print("  [dim]Dry-run mode — reply not sent.[/dim]")
        return

    if confirm("Send this reply?"):
        send_reply(
            service,
            thread_id=email["thread_id"],
            to=email["sender"],
            subject=email["subject"],
            body=draft,
        )
        console.print("  [bold green] Reply sent.[/bold green]")
    else:
        console.print("  [dim]Skipped.[/dim]")


def run_action_loop(
    service,
    emails: list[dict[str, Any]],
    analyses: list[dict[str, Any]],
    dry_run: bool = False,
    auto_archive: bool = False,
) -> None:
    """
    For each email, always offer all three actions: reply, label, archive.
    Nothing irreversible happens without explicit 'y'.
    """
    analysis_map = {a["id"]: a for a in analyses}

    for email in emails:
        analysis = analysis_map.get(email["id"], {})
        cat = analysis.get("category", "fyi")

        present_email(email, analysis)

        # Auto-archive newsletters without asking (only in auto-archive mode)
        if auto_archive and cat == "newsletter":
            if not dry_run:
                archive_message(service, email["id"])
                console.print("  [dim]Auto-archived newsletter.[/dim]")
            else:
                console.print("  [dim]Dry-run: would auto-archive newsletter.[/dim]")
            continue

        # Always offer all three actions
        if confirm("Draft and optionally send a reply?"):
            _handle_reply(service, email, dry_run)

        if confirm("Apply a label?"):
            label = Prompt.ask("  Label name", default=cat)
            if not dry_run:
                try:
                    apply_label(service, email["id"], label)
                    console.print(f"  [bold green]✓ Labelled '{label}'.[/bold green]")
                except Exception as e:
                    # "draft" is a protected system label name
                    console.print(f"  [bold red]Failed to apply label (possibly invalid name):[/bold red] {e}")
            else:
                console.print(f"  [dim]Dry-run: would apply label '{label}'.[/dim]")

        if confirm("Archive this email?"):
            if not dry_run:
                archive_message(service, email["id"])
                console.print("  [bold green]✓ Archived.[/bold green]")
            else:
                console.print("  [dim]Dry-run: would archive.[/dim]")

        console.print()


def print_summary_table(emails: list[dict], analyses: list[dict]) -> None:
    """Print a summary table of all fetched emails and their categories."""
    analysis_map = {a["id"]: a for a in analyses}

    table = Table(
        title="Inbox",
        box=box.SIMPLE_HEAD,
        title_style="bold cyan",
        header_style="bold dim",
        show_lines=False,
    )
    table.add_column("#", justify="right", style="dim", width=3)
    table.add_column("Category", width=16)
    table.add_column("P", justify="center", width=3)
    table.add_column("From", style="cyan", max_width=28)
    table.add_column("Subject", max_width=40)
    table.add_column("Summary")

    for i, email in enumerate(emails, 1):
        a = analysis_map.get(email["id"], {})
        cat = a.get("category", "?")
        color = CATEGORY_COLORS.get(cat, "white")
        table.add_row(
            str(i),
            Text(cat, style=color),
            str(a.get("priority", "-")),
            email["sender"].split("<")[0].strip(),
            email["subject"],
            a.get("summary", email["snippet"][:60]),
        )

    console.print()
    console.print(table)
