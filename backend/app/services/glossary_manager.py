import os
import json


class GlossaryManager:
    """
    Manages custom glossary terms for translation.
    Stores key-value pairs in a JSON file.
    """

    def __init__(self, glossary_path: str = "glossary.json"):
        self.glossary_path = glossary_path
        self.terms = self._load_glossary()

    def _load_glossary(self) -> dict:
        if not os.path.exists(self.glossary_path):
            return {}
        try:
            with open(self.glossary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading glossary: {e}")
            return {}

    def save_glossary(self, terms: dict):
        try:
            with open(self.glossary_path, "w", encoding="utf-8") as f:
                json.dump(terms, f, ensure_ascii=False, indent=2)
            self.terms = terms
            return True
        except Exception as e:
            print(f"Error saving glossary: {e}")
            return False

    def get_terms(self) -> dict:
        return self.terms

    def apply_glossary(self, text: str) -> str:
        """
        Applies glossary replacements to text.
        Simple string replacement (case-sensitive for now).
        """
        result = text
        for term, replacement in self.terms.items():
            if term and replacement:
                result = result.replace(term, replacement)
        return result
