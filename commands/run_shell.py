import subprocess
from rich import print as rprint
from rich.panel import Panel
import questionary
from memory import save_session_interaction, save_audit_log
from commands.base import BaseCommand

MAX_OUTPUT_LINES = 10

def get_head_output(text, lines=MAX_OUTPUT_LINES):
    all_lines = text.strip().splitlines()
    return "\n".join(all_lines[:lines]) + ("\n... [truncated]" if len(all_lines) > lines else "")

class RunShellCommand(BaseCommand):
    def execute(self):
        command = self.action["command"]
        reason = self.action.get("reason", "Bez uvedení důvodu.")
        full_output = self.action.get("full_output_required", False)

        rprint(Panel(f"[bold yellow]{command}[/bold yellow]", title="🤖 [magenta]AI navrhuje příkaz[/magenta]", style="blue"))
        rprint(f"[blue]📌 Důvod:[/blue] {reason}")

        if full_output:
            rprint("[yellow]⚠️ Tento příkaz bude mít plný výstup. Může být dlouhý.[/yellow]")

        decision = questionary.select(
            "Chceš tento příkaz provést?",
            choices=[
                "✅ Ano, spustit příkaz",
                "✏️ Upravit příkaz",
                "📝 Doplnit prompt",
                "⛔️ Zrušit akci"
            ]).ask()

        if decision.startswith("✅"):
            approved = True
            edited = False
        elif decision.startswith("✏️"):
            command = questionary.text("✏️ Uprav příkaz:", default=command).ask()
            approved = True
            edited = True
        elif decision.startswith("📝"):
            extra_prompt = questionary.text("📝 Doplnit prompt:").ask()
            save_session_interaction(self.session_id, "user", extra_prompt)
            return
        else:
            rprint("[red]⛔️ Zrušeno uživatelem.[/red]")
            return

        if approved:
            result = subprocess.getoutput(command)
            rprint(Panel(result, title="✅ [green]Výstup příkazu[/green]", style="cyan"))
            output = result if full_output else get_head_output(result)
            save_session_interaction(self.session_id, "shell_output", output)
            save_audit_log(command, approved, edited, self.session_id, True, result)