import questionary
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
import sys, yaml, time, os
from ai import query_ai
from memory import (
    save_session_interaction,
    load_session_history,
    save_audit_log,
    ensure_dirs_and_files,
    save_to_knowledge_base
)
from commands.run_shell import RunShellCommand
from commands.ask_user import AskUserCommand
from commands.done import DoneCommand

console = Console()

config = yaml.safe_load(open("config.yaml"))
language = config["language"]
trust_level = config["trust_level"]

handlers = {
    "run_shell": RunShellCommand,
    "ask_user": AskUserCommand,
    "done": DoneCommand
}

def get_latest_session_id():
    session_dir = "data/sessions"
    files = [f for f in os.listdir(session_dir) if f.endswith(".yaml")]
    if not files:
        return None
    latest = max(files, key=lambda f: int(f.replace(".yaml", "")))
    return latest.replace(".yaml", "")

def main():
    ensure_dirs_and_files()

    args = sys.argv[1:]
    if not args:
        rprint('[red]Použití:[/red] aia "[yellow]tvůj prompt[/yellow]" nebo [cyan]--continue / -c[/cyan] pro pokračování v poslední session.')
        sys.exit(1)

    if args[0] in ["--continue", "-c"]:
        session_id = get_latest_session_id()
        if not session_id:
            rprint("[red]❌ Nebyla nalezena žádná předchozí session.[/red]")
            sys.exit(1)
        rprint(f"[green]🔄 Pokračuji v session:[/green] {session_id}")
        save_session_interaction(session_id, "user", "Pokračuj, kde jsme skončili. Co mám udělat dál?")
    else:
        session_id = str(int(time.time()))
        user_prompt = args[0]
        save_session_interaction(session_id, "user", user_prompt)

    while True:
        history = load_session_history(session_id)
        messages = [
            {"role": "user" if msg["role"] == "shell_output" else msg["role"],
             "content": msg["content"]}
            for msg in history
        ]

        ai_response = query_ai(messages)
        save_session_interaction(session_id, "assistant", ai_response)

        try:
            action = yaml.safe_load(ai_response)
        except yaml.YAMLError as e:
            rprint(f"[red]❌ Chyba při parsování YAML:[/red] {e}")
            continue

        if not isinstance(action, dict) or "action" not in action:
            rprint("[red]❌ AI odpověď neobsahuje platnou akci.[/red]")
            rprint(action)
            continue

        if "remember" in action:
            save_to_knowledge_base(action["remember"])
            rprint(f"[cyan]🧠 Zapamatováno:[/cyan] {action['remember']}")

        action_type = action["action"]
        handler_class = handlers.get(action_type)

        if handler_class:
            handler_class(action, session_id).execute()
        else:
            rprint(f"[red]⚠️ Neznámá akce: {action_type}[/red]")
            break

if __name__ == "__main__":
    main()
