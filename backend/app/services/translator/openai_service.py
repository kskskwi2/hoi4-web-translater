import aiohttp
import os
from .base import BaseTranslator


class OpenAITranslatorService(BaseTranslator):
    """
    Translation using OpenAI API (GPT-4o-mini or GPT-4).
    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(
        self, model: str = "gpt-4o-mini", api_key: str = None, glossary: dict = None
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.glossary = glossary

    async def translate(self, text: str, target_lang: str) -> str:
        """Raw translation using OpenAI."""
        if not text or text.strip() == "":
            return text

        if not self.api_key:
            print("OpenAI API key not set!")
            return text

        lang_map = {"ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese"}
        target = lang_map.get(target_lang, target_lang)

        # Build Glossary Context
        glossary_text = ""
        if self.glossary:
            glossary_text = "\nGLOSSARY (Use these exact translations):\n"
            for k, v in self.glossary.items():
                glossary_text += f"- {k}: {v}\n"

        system_prompt = (
            f"You are a professional Hearts of Iron IV mod translator. Translate the text to {target}.\n"
            "RULES:\n"
            "1. Maintain specific HoI4 formatting codes (e.g., $VAR$, [Command], §Y...§!).\n"
            "2. Keep military and political context appropriate for WW2 era.\n"
            "3. DO NOT add explanations, notes, or quotes. Output ONLY the translation.\n"
            "4. If the text looks like a code key or filename, return it unchanged.\n"
            "5. Preserve newlines exactly.\n"
            f"{glossary_text}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                }
                async with session.post(
                    self.api_url, json=payload, headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"].strip()
                    else:
                        error = await resp.text()
                        print(f"OpenAI error: {resp.status} - {error}")
                        return text
        except Exception as e:
            print(f"OpenAI translation error: {e}")
            return text

    async def get_available_models(self) -> list:
        """Fetch available models from OpenAI API."""
        if not self.api_key:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(
                    "https://api.openai.com/v1/models", headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Filter for chat models
                        models = [
                            m["id"]
                            for m in data["data"]
                            if "gpt" in m["id"] and "instruct" not in m["id"]
                        ]
                        return sorted(models, reverse=True)
                    return []
        except Exception as e:
            print(f"Error fetching OpenAI models: {e}")
            return []
