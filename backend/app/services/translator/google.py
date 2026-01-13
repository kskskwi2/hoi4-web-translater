from googletrans import Translator
from .base import BaseTranslator
import asyncio


class GoogleTranslatorService(BaseTranslator):
    def __init__(self):
        self.translator = Translator()

    async def translate(self, text: str, target_lang: str) -> str:
        """Raw translation - called by translate_with_preservation in base."""
        if not text or text.strip() == "":
            return text

        # Don't catch exceptions here; let the base class retry logic handle it
        loop = asyncio.get_event_loop()

        # Add timeout to prevent hanging
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None, lambda: self.translator.translate(text, dest=target_lang)
                ),
                timeout=10.0,  # 10 seconds timeout per request
            )
            return result.text
        except asyncio.TimeoutError:
            raise Exception("Google Translate API timed out")
