import aiohttp
from .base import BaseTranslator


class OllamaTranslatorService(BaseTranslator):
    """
    Translation using local Ollama instance.
    Requires Ollama running locally with a model like llama2, mistral, gemma, etc.
    Note: Ollama returns NDJSON streaming, we need to handle that.
    """

    SUPPORTS_NATIVE_GLOSSARY = True

    def __init__(
        self,
        model: str = "gemma2",
        base_url: str = "http://localhost:11434",
        glossary: dict = None,
    ):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/chat"  # Changed to /api/chat for better prompt handling with system role
        self.glossary = glossary

    async def translate(self, text: str, target_lang: str) -> str:
        """Raw translation using Ollama."""
        if not text or text.strip() == "":
            return text

        lang_map = {
            "ko": "Korean",
            "en": "English",
            "ja": "Japanese",
            "zh": "Chinese",
            "zh-CN": "Chinese Simplified",
            "zh-TW": "Chinese Traditional",
        }
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

        system_content = (
            f"{ho4_official_guide}\\n"
            f"4. **Glossary (User Provided)**:\\n{glossary_text}\\n\\n"
            f"Translate the following text to {target}:"
        )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": text},
        ]

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Lower temperature to prevent hallucinations
                        "num_predict": 2048,
                    },
                }
                headers = {"Content-Type": "application/json"}

                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status == 200:
                        # Skip content-type check because Ollama sometimes returns text/plain for JSON
                        data = await resp.json(content_type=None)

                        # Ollama chat API response format
                        result_text = text
                        if "message" in data:
                            result_text = data["message"]["content"]
                        elif "response" in data:
                            result_text = data["response"]

                        return self.clean_thinking_content(result_text)
                    elif resp.status == 404:
                        print(
                            f"Ollama error: 404 (Model '{self.model}' not found? Try 'ollama pull {self.model}')"
                        )
                        return text
                    else:
                        print(f"Ollama error: {resp.status} - {await resp.text()}")
                        return text
        except Exception as e:
            print(f"Ollama translation error: {e}")
            return text

    async def get_available_models(self) -> list:
        """Fetch available models from Ollama API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/tags"
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        # Format: {"models": [{"name": "gemma2:latest", ...}]}
                        models = [m["name"] for m in data.get("models", [])]
                        return sorted(models)
                    else:
                        print(f"Ollama fetch models error: {resp.status}")
                        return []
        except Exception as e:
            print(f"Error fetching Ollama models: {e}")
            return []
