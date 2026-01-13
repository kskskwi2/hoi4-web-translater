import aiohttp
import os
from .base import BaseTranslator


class ClaudeTranslatorService(BaseTranslator):
    """
    Translation using Anthropic Claude API.
    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: str = None,
        glossary: dict = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.glossary = glossary

    async def translate(self, text: str, target_lang: str) -> str:
        """Raw translation using Claude."""
        if not text or text.strip() == "":
            return text

        if not self.api_key:
            print("Anthropic API key not set!")
            return text

        lang_map = {"ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese"}
        target = lang_map.get(target_lang, target_lang)

        glossary_text = ""
        if self.glossary:
            glossary_text = "\nGLOSSARY (Use these exact translations):\n"
            for k, v in self.glossary.items():
                glossary_text += f"- {k}: {v}\n"

        system_instruction = (
            f"Translate to {target}. RULES:\n"
            "- Keep HoI4 variables/codes ($VAR$, §Y) intact.\n"
            "- Use WW2 military/political tone.\n"
            "- Output ONLY translation."
            f"{glossary_text}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.model,
                    "max_tokens": 1024,
                    "system": system_instruction,
                    "messages": [{"role": "user", "content": text}],
                }
                async with session.post(
                    self.api_url, json=payload, headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["content"][0]["text"].strip()
                    else:
                        error = await resp.text()
                        print(f"Claude error: {resp.status} - {error}")
                        return text
        except Exception as e:
            print(f"Claude translation error: {e}")
            return text
