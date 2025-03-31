import questionary
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
import sys, uuid, yaml, subprocess, time
from ai import query_ai
from memory import (
    save_session_interaction,
    load_session_history,
    save_audit_log,
    ensure_dirs_and_files,
    save_to_knowledge_base,
    load_yaml,
    KB_FILE
)


console = Console()

config = yaml.safe_load(open("config.yaml"))
language = config["language"]
trust_level = config["trust_level"]

MAX_OUTPUT_LINES = 10

def get_head_of_output(text, lines=MAX_OUTPUT_LINES):
    all_lines = text.strip().splitlines()
    return "\n".join(all_lines[:lines]) + ("\n... [truncated]" if len(all_lines) > lines else "")

def run_shell_command(command):
    rprint("[bold green]🚀 Spouštím příkaz...[/bold green]\n")
    result = subprocess.getoutput(command)
    console.print(Panel(result, title="✅ [green]Výstup příkazu[/green]", style="cyan"))
    return result

def main():
    ensure_dirs_and_files()

    if len(sys.argv) != 2:
        rprint('[red]Použití:[/red] aia "[yellow]tvůj prompt[/yellow]"')
        sys.exit(1)

    session_id = str(int(time.time()))  # Unix timestamp jako ID session
    user_prompt = sys.argv[1]
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

        if "remember" in action:
            save_to_knowledge_base(action["remember"])
            rprint(f"[cyan]🧠 Zapamatováno:[/cyan] {action['remember']}")

        if action["action"] == "run_shell":
            command = action["command"]
            reason = action.get("reason", "Bez uvedení důvodu.")

            console.print(Panel(f"[bold yellow]{command}[/bold yellow]", title="🤖 [magenta]AI navrhuje příkaz[/magenta]", style="blue"))
            rprint(f"[blue]📌 Důvod:[/blue] {reason}")

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
                extra_prompt = questionary.text("📝 Doplňující prompt:").ask()
                save_session_interaction(session_id, "user", extra_prompt)
                continue
            else:
                approved = False
                edited = False
                rprint("[red]⛔️ Zrušeno uživatelem.[/red]")
                return

            if approved:
                result = run_shell_command(command)
                truncated_result = get_head_of_output(result)
                save_session_interaction(session_id, "shell_output", truncated_result)
                save_audit_log(command, approved, edited, session_id, True, result)

        elif action["action"] == "ask_user":
            question = action["question"]
            answer = questionary.text(f"❓ {question}").ask()
            save_session_interaction(session_id, "user", answer)

        elif action["action"] == "done":
            message = action["message"]
            rprint(f"\n✨ [green]AI:[/green] {message}")
            break

        else:
            rprint("[red]⚠️ Neznámá akce.[/red]")
            break

if __name__ == "__main__":
    main()