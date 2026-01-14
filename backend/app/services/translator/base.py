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
        if text is None:
            return ""
        result = text
        for placeholder, original, _ in extractions:
            result = result.replace(placeholder, original)
        return result

    def clean_thinking_content(self, text: str) -> str:
        """
        Removes <think>...</think> blocks from the text.
        Useful for reasoning models (like DeepSeek R1) that output their thought process.
        """
        if not text:
            return text

        # Remove <think>...</think> content (case insensitive, dotall)
        # We use a non-greedy match .*? to avoid eating the whole string if multiple tags exist (unlikely but safe)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)

        return text.strip()

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

    def apply_glossary_as_variables(
        self, text: str, glossary: dict
    ) -> tuple[str, list]:
        """
        Replaces glossary keys in text with placeholders.
        Returns (modified_text, list_of_extractions)
        """
        extractions = []
        modified = text
        placeholder_idx = 0

        # Sort keys by length (descending) to avoid partial matching issues
        sorted_keys = sorted(glossary.keys(), key=len, reverse=True)

        for key in sorted_keys:
            if not key or not key.strip():
                continue

            # Case-insensitive search
            pattern = re.escape(key)
            matches = list(re.finditer(pattern, modified, re.IGNORECASE))

            for match in reversed(matches):
                original_text_in_source = match.group(0)
                target_val = glossary[key]

                # Use a placeholder that AI is likely to preserve but distinct from VAR
                placeholder = f"__GLS{placeholder_idx}__"
                extractions.append((placeholder, target_val, "GLOSSARY"))

                modified = (
                    modified[: match.start()] + placeholder + modified[match.end() :]
                )
                placeholder_idx += 1

        return modified, extractions

    async def translate_with_preservation(
        self, text: str, target_lang: str, glossary: dict = None
    ) -> str:
        """
        Translates text while preserving HOI4 variables.
        """
        if not text or text.strip() == "":
            return text

        # 1. Extract HOI4 Variables (Code preservation)
        cleaned_text, var_extractions = self.extract_variables(text)

        # 2. Extract Glossary Terms (Term enforcement)
        # Only apply strict variable replacement if the translator DOES NOT support native glossary context
        glossary_extractions = []
        supports_native_glossary = getattr(self, "SUPPORTS_NATIVE_GLOSSARY", False)

        if glossary and not supports_native_glossary:
            cleaned_text, glossary_extractions = self.apply_glossary_as_variables(
                cleaned_text, glossary
            )

        # 3. Translate with Retry
        try:
            translated = await self.translate_with_retry(cleaned_text, target_lang)
        except Exception:
            return text  # Fallback to original on total failure

        # 4. Restore Glossary Terms (Inject Target Value)
        # Note: We use restore_variables logic but with glossary list
        if glossary_extractions:
            translated = self.restore_variables(translated, glossary_extractions)

        # 5. Restore HOI4 Variables (Inject Original Code)
        restored = self.restore_variables(translated, var_extractions)

        return restored
