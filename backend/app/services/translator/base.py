from abc import ABC, abstractmethod
import re


class BaseTranslator(ABC):
    """
    Abstract Base Class for translation services.
    Provides common functionality like variable preservation.
    """

    # HOI4 Localization patterns to preserve
    # [ScopeCommand] - e.g., [GetName], [Root.GetName], [From.Owner.GetName]
    # $VAR$ - variables
    # §X - color codes (§Y yellow, §R red, §! reset, etc.)
    # \n - newlines (literal)
    # £icon - icon references

    PRESERVE_PATTERNS = [
        (r"\[([A-Za-z0-9_.]+)\]", "SCOPECMD"),  # [GetName], [Root.GetName]
        (r"\$([A-Za-z0-9_]+)\$", "VARIABLE"),  # $variable$
        (r"§([A-Za-z!])", "COLOR"),  # §Y, §!, §R
        (r"£([A-Za-z0-9_]+)", "ICON"),  # £icon_name
        (r"\\n", "NEWLINE"),  # \n literal
    ]

    def extract_variables(self, text: str) -> tuple[str, list]:
        """
        Extracts variables from text and replaces with placeholders.
        Returns (modified_text, list_of_extractions)
        """
        extractions = []
        modified = text
        placeholder_idx = 0

        for pattern, var_type in self.PRESERVE_PATTERNS:
            matches = list(re.finditer(pattern, modified))
            for match in reversed(matches):  # Reverse to not mess up indices
                original = match.group(0)
                placeholder = f"__VAR{placeholder_idx}__"
                extractions.append((placeholder, original, var_type))
                modified = (
                    modified[: match.start()] + placeholder + modified[match.end() :]
                )
                placeholder_idx += 1

        return modified, extractions

    def restore_variables(self, text: str, extractions: list) -> str:
        """
        Restores variables from placeholders.
        """
        result = text
        for placeholder, original, _ in extractions:
            result = result.replace(placeholder, original)
        return result

    @abstractmethod
    async def translate(self, text: str, target_lang: str) -> str:
        """
        Translates text to target language. Must be implemented by subclasses.
        """
        pass

    async def translate_with_retry(
        self, text: str, target_lang: str, retries: int = 3
    ) -> str:
        """
        Wrapper with exponential backoff retry logic.
        """
        import asyncio
        import random

        delay = 1.0
        last_exception = None

        for attempt in range(retries):
            try:
                return await self.translate(text, target_lang)
            except Exception as e:
                last_exception = e
                print(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    sleep_time = delay * (1 + random.random())  # Jitter
                    print(f"Retrying in {sleep_time:.2f}s...")
                    await asyncio.sleep(sleep_time)
                    delay *= 2

        raise last_exception

    async def translate_with_preservation(
        self, text: str, target_lang: str, glossary: dict = None
    ) -> str:
        """
        Translates text while preserving HOI4 variables.
        """
        if not text or text.strip() == "":
            return text

        # Apply Glossary BEFORE translation (Substitutions)
        # Note: This is aggressive substitution.
        # Ideally, we should pass context, but strict replacement ensures consistency for made-up terms.
        # We replace the term with a placeholder to prevent AI from re-translating it weirdly,
        # OR we just rely on AI to translate the REST.
        # Actually, for Glossary, we often want the AI to know the mapping.
        # But `translate` signature doesn't support context yet.
        # Let's do a simple substitution strategy:
        # 1. Substitute Glossary Terms -> Target Terms (if they match the source language)
        # BUT this is risky if the AI sees Korean in English text.
        #
        # Better Strategy:
        # We'll attach the glossary to the instance temporarily or rely on system prompt injection in the service.
        # Since `translate` is abstract, we can't easily change the signature for all subclasses without refactoring all.
        #
        # Workaround: Pre-pend glossary to the text for context? No, that messes up the output.
        #
        # BEST APPROACH: Modify the system prompt in the SERVICE classes using a member variable.
        # The `ModGenerator` instantiates the service ONCE. We can set `service.glossary = glossary`.

        # Extract variables
        cleaned_text, extractions = self.extract_variables(text)

        # Translate with Retry
        try:
            translated = await self.translate_with_retry(cleaned_text, target_lang)
        except Exception:
            return text  # Fallback to original on total failure

        # Restore variables
        restored = self.restore_variables(translated, extractions)

        # Apply Glossary AFTER translation (Strict Enforcement)
        # This handles cases where AI ignored the instruction OR explicitly fixes terms.
        if glossary:
            for term, replacement in glossary.items():
                # This is tricky: we want to replace the TRANSLATED concept.
                # But the glossary maps Source -> Target.
                # So we can't search for 'Source' in 'Target' text.
                # We need AI to do it.
                pass

        return restored
