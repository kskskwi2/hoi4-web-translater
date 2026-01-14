import aiohttp
import os
import asyncio
import re
from .base import BaseTranslator


class GeminiTranslatorService(BaseTranslator):
    """
    Translation using Google Gemini API.
    Requires GEMINI_API_KEY environment variable.
    """

    SUPPORTS_NATIVE_GLOSSARY = True

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

        prompt = (
            f"{ho4_official_guide}\\n"
            f"4. **Glossary (User Provided)**:\\n{glossary_text}\\n\\n"
            f"Translate the following text to {target}:\\n{text}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.api_url}?key={self.api_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}

                max_retries = 5
                base_delay = 2

                for attempt in range(max_retries):
                    async with session.post(url, json=payload) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if "candidates" in data and data["candidates"]:
                                raw_text = data["candidates"][0]["content"]["parts"][0][
                                    "text"
                                ]
                                return self.clean_thinking_content(raw_text)
                            else:
                                print(f"Gemini empty response: {data}")
                                return text
                        elif resp.status == 429:
                            error_text = await resp.text()
                            # Extract retry delay if available
                            # Pattern: "Please retry in 14.046314639s."
                            retry_match = re.search(
                                r"retry in (\d+(\.\d+)?)s", error_text
                            )
                            if retry_match:
                                delay = (
                                    float(retry_match.group(1)) + 1.0
                                )  # Add 1s buffer
                            else:
                                delay = base_delay * (2**attempt)  # Exponential backoff

                            print(
                                f"Gemini 429 Rate Limit. Retrying in {delay:.2f}s... (Attempt {attempt + 1}/{max_retries})"
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            error = await resp.text()
                            print(f"Gemini error: {resp.status} - {error}")
                            return text

                print("Gemini: Max retries exceeded.")
                return text

        except Exception as e:
            print(f"Gemini translation error: {e}")
            return text

    async def get_available_models(self) -> list:
        """Fetch available models from Google Gemini API."""
        # User requested specific models:
        user_preferred = [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-exp-1206",
        ]

        if not self.api_key:
            return user_preferred

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        api_models = [
                            m["name"].replace("models/", "")
                            for m in data.get("models", [])
                            if "generateContent"
                            in m.get("supportedGenerationMethods", [])
                        ]

                        # Combine: User preferred first, then API findings
                        seen = set()
                        final_list = []
                        for m in user_preferred + api_models:
                            if m not in seen:
                                final_list.append(m)
                                seen.add(m)
                        return final_list
                    else:
                        print(
                            f"Gemini fetch models error: {resp.status} - {await resp.text()}"
                        )
                        return user_preferred
        except Exception as e:
            print(f"Error fetching Gemini models: {e}")
            return user_preferred

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Filter for models that support generateContent
                        models = [
                            m["name"].replace("models/", "")
                            for m in data.get("models", [])
                            if "generateContent"
                            in m.get("supportedGenerationMethods", [])
                        ]

                        # Add user-requested manual models
                        manual_models = ["gemini-3-pro", "gemini-2.5-flash"]
                        models.extend(manual_models)

                        # Deduplicate and sort
                        return sorted(list(set(models)), reverse=True)
                    else:
                        print(
                            f"Gemini fetch models error: {resp.status} - {await resp.text()}"
                        )
                        return []
        except Exception as e:
            print(f"Error fetching Gemini models: {e}")
            return []
