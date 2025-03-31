import questionary
from memory import save_session_interaction
from commands.base import BaseCommand

class AskUserCommand(BaseCommand):
    def execute(self):
        question = self.action["question"]
        answer = questionary.text(f"❓ {question}").ask()
        save_session_interaction(self.session_id, "user", answer)