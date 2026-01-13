import aiohttp
import os
from .base import BaseTranslator


class GeminiTranslatorService(BaseTranslator):
    """
    Translation using Google Gemini API.
    Requires GEMINI_API_KEY environment variable.
    """

    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        api_key: str = None,
        glossary: dict = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        self.glossary = glossary

    async def translate(self, text: str, target_lang: str) -> str:
        """Raw translation using Gemini."""
        if not text or text.strip() == "":
            return text

        if not self.api_key:
            print("Gemini API key not set!")
            return text

        lang_map = {"ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese"}
        target = lang_map.get(target_lang, target_lang)

        glossary_text = ""
        if self.glossary:
            glossary_text = "\nGLOSSARY (Use these exact translations):\n"
            for k, v in self.glossary.items():
                glossary_text += f"- {k}: {v}\n"

        prompt = (
            f"Task: Translate HoI4 mod text to {target}.\n"
            f"Rules: Preserve special codes (§, $, []). No explanations. WW2 Context.\n"
            f"{glossary_text}"
            f"Text to translate:\n{text}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}?key={self.api_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["candidates"][0]["content"]["parts"][0][
                            "text"
                        ].strip()
                    else:
                        error = await resp.text()
                        print(f"Gemini error: {resp.status} - {error}")
                        return text
        except Exception as e:
            print(f"Gemini translation error: {e}")
            return text
