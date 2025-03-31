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
    def __init__(self, action, session_id):
        super().__init__(action, session_id)
        self.command = action["command"]
        self.reason = action.get("reason", "Bez uvedení důvodu.")
        self.full_output = action.get("full_output_required", False)
        self.edited = False

    def execute(self):
        self._show_proposal()
        if self._get_user_approval():
            self._execute_command()

    def _show_proposal(self):
        rprint(Panel(f"[bold yellow]{self.command}[/bold yellow]", title="🤖 [magenta]AI navrhuje příkaz[/magenta]", style="blue"))
        rprint(f"[blue]📌 Důvod:[/blue] {self.reason}")
        if self.full_output:
            rprint("[yellow]⚠️ Tento příkaz bude mít plný výstup. Může být dlouhý.[/yellow]")

    def _get_user_approval(self):
        options = {
            "✅ Ano, spustit příkaz": self._approve,
            "✏️ Upravit příkaz": self._edit,
            "📝 Doplnit prompt": self._add_prompt,
            "⛔️ Zrušit akci": self._cancel
        }

        decision = questionary.select("Chceš tento příkaz provést?", choices=list(options.keys())).ask()
        return options[decision]()

    def _approve(self):
        self.edited = False
        return True

    def _edit(self):
        self.command = questionary.text("✏️ Uprav příkaz:", default=self.command).ask()
        self.edited = True
        return True

    def _add_prompt(self):
        extra_prompt = questionary.text("📝 Doplnit prompt:").ask()
        save_session_interaction(self.session_id, "user", extra_prompt)
        return False

    def _cancel(self):
        rprint("[red]⛔️ Zrušeno uživatelem.[/red]")
        return False

    def _execute_command(self):
        result = subprocess.getoutput(self.command)
        rprint(Panel(result, title="✅ [green]Výstup příkazu[/green]", style="cyan"))
        output = result if self.full_output else get_head_output(result)
        save_session_interaction(self.session_id, "shell_output", output)
        save_audit_log(self.command, self.edited, self.session_id, True, result)