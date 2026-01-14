import aiohttp
import os
from .base import BaseTranslator


class OpenAITranslatorService(BaseTranslator):
    """
    Translation using OpenAI API (GPT-4o-mini or GPT-4).
    Requires OPENAI_API_KEY environment variable.
    """

    SUPPORTS_NATIVE_GLOSSARY = True

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

        ho4_official_guide = (
            "You are the Lead Korean Localizer for Paradox Interactive's 'Hearts of Iron IV'.\\n"
            "Your mandate is to translate game text from English to Korean, STRICTLY following the official localization standards found in the game's `localisation/korean` folder.\\n\\n"
            "***OFFICIAL HOI4 KOREAN STYLE GUIDE***\\n\\n"
            "1. **Tone & Grammar (CRITICAL)**:\\n"
            "   - **Narrative/Descriptions (Events, Lore)**: Use formal 'Hapsho-che' (합쇼체, ~습니다). It must sound like a 1940s military report, diplomatic cable, or historical record. Dry, serious, and professional.\\n"
            "   - **Tooltips/Effects/Modifiers**: Use concise Noun Endings (~함, ~임, ~증가, ~감소). NEVER use full sentences here. (e.g., 'Gain 50 PP' -> '정치력 50 획득', not '획득합니다')\\n"
            "   - **Interface/Buttons/Options**: Use concise Plain Form (해라체, ~다) or Noun Phrases.\\n\\n"
            "2. **Mandatory Terminology (Do NOT deviate)**:\\n"
            "   - Manpower -> 인력\\n"
            "   - Stability -> 안정도\\n"
            "   - War Support -> 전쟁 지지도\\n"
            "   - Organization -> 조직력\\n"
            "   - Division -> 사단 (Military Unit)\\n"
            "   - Infrastructure -> 기반시설\\n"
            "   - Factory -> 공장\\n"
            "   - Equipment -> 장비\\n"
            "   - Civilian Industry -> 민간 산업\\n"
            "   - Army -> 육군 (Specific branch), 군 (General)\\n"
            "   - Navy -> 해군\\n"
            "   - Air force -> 공군\\n"
            "   - Cheat -> 치트\\n"
            "   - Buff -> 버프\\n"
            "   - Debuff -> 디버프\\n"
            "   - National Focus -> 국가 중점\\n\\n"
            "3. **Formatting & Safety**:\\n"
            "   - **PRESERVE** all special codes: §Y, §R, §G, §!, $VAR$, [Root.GetName], £icon£, \\n.\\n"
            "   - **NO CHINESE CHARACTERS (Hanja)**: Use Korean Hangul ONLY unless the source is explicitly Chinese.\\n"
            "   - **NO THINKING**: Do not output your thought process. Output ONLY the final translated text.\\n"
            "   - **Keys**: If the input looks like a code key (e.g., `political_power_gain`), return it unchanged.\\n"
        )

        system_prompt = (
            f"{ho4_official_guide}\\n"
            f"4. **Glossary (User Provided)**:\\n{glossary_text}\\n\\n"
            f"Translate the following text to {target}:"
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
                        raw_text = data["choices"][0]["message"]["content"]
                        return self.clean_thinking_content(raw_text)
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
