import yaml, os
from datetime import datetime

config = yaml.safe_load(open("config.yaml"))

DATA_DIR = config.get("data_dir", "./data")
KB_FILE = os.path.join(DATA_DIR, "knowledge_base.yaml")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "audit_log.yaml")
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")

def ensure_dirs_and_files():
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    for file in [KB_FILE, AUDIT_LOG_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                f.write("# Automatically created by aia\n")

def load_yaml(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_yaml(data, file_path):
    with open(file_path, 'w') as f:
        yaml.dump(data, f)

def save_to_knowledge_base(info):
    kb = load_yaml(KB_FILE)
    if 'memory' not in kb:
        kb['memory'] = []
    if info not in kb['memory']:
        kb['memory'].append(info)
    save_yaml(kb, KB_FILE)

def save_audit_log(command, approved, edited, session_id, ai_generated, result):
    log = load_yaml(AUDIT_LOG_FILE)
    if "audit" not in log:
        log["audit"] = []
    log["audit"].append({
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "approved_by_user": approved,
        "edited_by_user": edited,
        "session_id": session_id,
        "ai_generated": ai_generated,
        "result": result
    })
    save_yaml(log, AUDIT_LOG_FILE)

def save_session_interaction(session_id, role, content):
    session_file = os.path.join(SESSIONS_DIR, f"{session_id}.yaml")
    session = load_yaml(session_file)
    if "interactions" not in session:
        session["interactions"] = []
    session["interactions"].append({"role": role, "content": content})
    save_yaml(session, session_file)

def load_session_history(session_id):
    session_file = os.path.join(SESSIONS_DIR, f"{session_id}.yaml")
    return load_yaml(session_file).get("interactions", [])

def check_and_remember_unavailable_tools(ai, shell_output):
    prompts = yaml.safe_load(open("prompts.yaml"))
    prompt = prompts["remember_instruction"].format(shell_output=shell_output)

    response = ai([{"role": "system", "content": prompt}])
    parsed_response = yaml.safe_load(response)

    if parsed_response.get("remember"):
        save_to_knowledge_base(parsed_response["info"])