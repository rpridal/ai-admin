from openai import OpenAI
import yaml

config = yaml.safe_load(open("config.yaml"))
prompts = yaml.safe_load(open("prompts.yaml"))

client = OpenAI(api_key=config["openai_api_key"])

def query_ai(messages):
    system_instruction = prompts["system_instruction"]

    full_messages = [{"role": "system", "content": system_instruction}] + messages

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=full_messages,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()