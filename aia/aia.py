import sys, uuid, yaml, subprocess
from ai import query_ai
from memory import (
    save_session_interaction,
    load_session_history,
    save_audit_log,
    ensure_dirs_and_files
)

config = yaml.safe_load(open("config.yaml"))
language = config["language"]
trust_level = config["trust_level"]

def run_shell_command(command):
    print(f"Executing: {command}")
    result = subprocess.getoutput(command)
    print(result)
    return result

def main():
    ensure_dirs_and_files()

    if len(sys.argv) != 2:
        print('Usage: aia "your prompt"')
        sys.exit(1)

    session_id = uuid.uuid4().hex[:6]
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

        action = yaml.safe_load(ai_response)

        if action["action"] == "run_shell":
            command = action["command"]
            print(f"AI navrhuje příkaz: {command}")

            if trust_level in ["low", "medium"]:
                decision = input("Approve [y], Edit [e], Cancel [n]? ")
                if decision == "y":
                    approved = True
                    edited = False
                elif decision == "e":
                    command = input("Edit command: ")
                    approved = True
                    edited = True
                else:
                    approved = False
                    edited = False
                    print("Cancelled by user.")
                    return
            else:
                approved = True
                edited = False

            if approved:
                result = run_shell_command(command)
                save_session_interaction(session_id, "shell_output", result)
                save_audit_log(command, approved, edited, session_id, True, result)

        elif action["action"] == "ask_user":
            question = action["question"]
            answer = input(f"AI asks: {question}\nYour answer: ")
            save_session_interaction(session_id, "user", answer)

            # Pokračuj v cyklu (AI dostane novou odpověď uživatele a rozhodne co dál)

        elif action["action"] == "done":
            print(action["message"])
            break  # hotovo, ukončíme cyklus

        else:
            print("Unknown action.")
            break

if __name__ == "__main__":
    main()