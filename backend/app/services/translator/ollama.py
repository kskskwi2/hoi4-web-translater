import aiohttp
from .base import BaseTranslator


class OllamaTranslatorService(BaseTranslator):
    """
    Translation using local Ollama instance.
    Requires Ollama running locally with a model like llama2, mistral, gemma, etc.
    Note: Ollama returns NDJSON streaming, we need to handle that.
    """

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

        system_content = (
            f"You are a professional Hearts of Iron IV mod translator. Translate the text to {target}.\n"
            "RULES:\n"
            "1. Output ONLY the translation. No 'Here is the translation' or notes.\n"
            "2. Preserve HoI4 special codes ($VAR$, [Command], §Y...§!).\n"
            f"{glossary_text}"
        )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": text},
        ]

        try:
            async with aiohttp.ClientSession() as session:
                payload = {"model": self.model, "messages": messages, "stream": False}
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
                        if "message" in data:
                            return data["message"]["content"].strip()
                        elif "response" in data:
                            return data["response"].strip()
                        return text
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
