import yaml, re, logging, json, os
from datetime import datetime
from openai import OpenAI
from memory import load_yaml, KB_FILE

os.makedirs("logs", exist_ok=True)

# --- JSON logger setup ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }
        return json.dumps(log_record, ensure_ascii=False)

logger = logging.getLogger("chat_logger")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("logs/chat.log")
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
# --------------------------

config = yaml.safe_load(open("config.yaml"))
prompts = yaml.safe_load(open("prompts.yaml"))
client = OpenAI(api_key=config["openai_api_key"])

def clean_response(text):
    return re.sub(r'^```.*?\n|```$', '', text, flags=re.DOTALL).strip()

def query_ai(messages):
    knowledge_base = load_yaml(KB_FILE)
    knowledge_base_str = yaml.dump(knowledge_base)

    system_instruction = prompts["system_instruction"].format(
        knowledge_base=knowledge_base_str
    )

    full_messages = [
        {"role": "system", "content": system_instruction},
        *messages
    ]

    logger.info(f"Request: {full_messages}")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=full_messages,
        temperature=0.3
    )

    raw_content = response.choices[0].message.content.strip()
    cleaned = clean_response(raw_content)

    logger.info(f"Response: {cleaned}")

    return cleaned
