from ai.openai_provider import OpenAIProvider
from memory import load_config

config = load_config()
ai_provider = OpenAIProvider(config)
