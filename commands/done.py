import sys
from rich import print as rprint
from commands.base import BaseCommand

class DoneCommand(BaseCommand):
    def execute(self):
        message = self.action["message"]
        rprint(f"\n✨ [green]AI:[/green] {message}")
        sys.exit(0)