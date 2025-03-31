import yaml, re, logging, json, os
from datetime import datetime
from openai import OpenAI
from memory import load_yaml, KB_FILE
from ai.base_provider import BaseAIProvider
from rich import print as rprint

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

prompts = yaml.safe_load(open("prompts.yaml"))

class OpenAIProvider(BaseAIProvider):
    def __init__(self, config):
    #self.primary_model = "gpt-3.5-turbo-0125"
        self.primary_model = "gpt-4o"
        self.fallback_model = "gpt-4o"
        self.client = OpenAI(api_key=config.get("openai_api_key"))

    def query(self, messages, mode="fast"):
        if mode == "smart":
            rprint(f"🤖 Dotazuji se modelu: [bold cyan]{self.fallback_model}[/bold cyan]")
            return self._send_request(messages, self.fallback_model)

        rprint(f"🤖 Dotazuji se modelu: [bold green]{self.primary_model}[/bold green]")
        response = self._send_request(messages, self.primary_model)

        try:
            parsed = yaml.safe_load(response)
            if isinstance(parsed, dict) and parsed.get("action") == "switch_model":
                reason = parsed.get("reason", "Neznámý důvod")
                rprint(f"\n[🔁 Přepínám na {self.fallback_model} – důvod: {reason}]")
                return self._send_request(messages, self.fallback_model)
        except yaml.YAMLError:
            pass

        return response

    def _send_request(self, messages, model):
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

        response = self.client.chat.completions.create(
            model=model,
            messages=full_messages,
            temperature=0.3
        )

        raw_content = response.choices[0].message.content.strip()
        cleaned = self._clean_response(raw_content)

        logger.info(f"Response: {cleaned}")
        return cleaned

    def _clean_response(self, text):
        return re.sub(r'^```.*?\n|```$', '', text, flags=re.DOTALL).strip()