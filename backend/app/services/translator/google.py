try:
    from googletrans import Translator as GoogleTrans
except ImportError:
    GoogleTrans = None
    print("Warning: googletrans not available (incompatible httpcore/httpx)")
except AttributeError:
    GoogleTrans = None
    print("Warning: googletrans broken due to httpcore version mismatch")

from deep_translator import GoogleTranslator as DeepGoogle
from .base import BaseTranslator
import asyncio
import random


class GoogleTranslatorService(BaseTranslator):
    def __init__(self):
        # We don't maintain a persistent connection anymore to avoid state issues
        pass

    async def translate(self, text: str, target_lang: str) -> str:
        """Raw translation - called by translate_with_preservation in base."""
        if not text or text.strip() == "":
            return text

        loop = asyncio.get_event_loop()

        # Strategy 1: Try deep-translator first (more reliable recently)
        try:

            def _deep_translate():
                return DeepGoogle(source="auto", target=target_lang).translate(text)

            result = await asyncio.wait_for(
                loop.run_in_executor(None, _deep_translate), timeout=10.0
            )
            return result
        except Exception as e1:
            # print(f"DeepTranslator failed: {e1}, falling back to googletrans...")
            pass

        # Strategy 2: Fallback to googletrans (legacy)
        try:

            def _googletrans_translate():
                t = GoogleTrans()
                return t.translate(text, dest=target_lang).text

            result = await asyncio.wait_for(
                loop.run_in_executor(None, _googletrans_translate), timeout=10.0
            )
            return result
        except asyncio.TimeoutError:
            raise Exception("Google Translate API timed out (both strategies)")
        except Exception as e:
            # googletrans sometimes raises weird errors or SSL errors
            # We want to re-raise them so the retry logic catches them
            raise Exception(f"Google Translate API Error: {str(e)}")
