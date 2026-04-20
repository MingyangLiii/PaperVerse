import os
from openai import OpenAI


class LLM:
    def __init__(self):
        self.client = OpenAI(
            api_key="",
            base_url="https://api.deepseek.com"
            )

    def chat(self, messages, stream=False):
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=stream
        )
        return response.choices[0].message.content

