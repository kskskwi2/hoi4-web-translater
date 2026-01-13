import os
import re


class VanillaManager:
    """
    Manages the 'Translation Memory' from the Vanilla game.
    Reads English and Target Language (e.g. Korean) files from HoI4 installation
    and creates a mapping: English Value -> Target Value.
    """

    def __init__(self, vanilla_path: str, target_lang: str = "korean"):
        self.vanilla_path = vanilla_path
        self.target_lang = target_lang
        self.translation_memory = {}  # { "English Text": "Korean Text" }
        self.entry_pattern = re.compile(
            r'^\s*([a-zA-Z0-9_\.\-]+)(:\d+)?:?\s*"(.*)"(.*)$'
        )

    def load_database(self):
        """
        Scans all localisation files in vanilla path and builds the database.
        """
        if not self.vanilla_path or not os.path.exists(self.vanilla_path):
            print(f"Vanilla path not found: {self.vanilla_path}")
            return

        print(f"Loading Vanilla database from: {self.vanilla_path}")

        # Paths
        loc_path = os.path.join(self.vanilla_path, "localisation")
        english_path = os.path.join(loc_path, "english")

        # Determine target folder (e.g., korean)
        # Assuming vanilla follows standard structure
        target_path = os.path.join(loc_path, self.target_lang)

        if not os.path.exists(english_path) or not os.path.exists(target_path):
            print(f"Vanilla localisation folders not found in {loc_path}")
            return

        # Scan English files
        english_files = {}  # { filename_base: { key: value } }

        for root, _, files in os.walk(english_path):
            for file in files:
                if file.endswith("l_english.yml"):
                    base_name = file.replace("_l_english.yml", "")
                    file_path = os.path.join(root, file)
                    english_files[base_name] = self._parse_file(file_path)

        # Scan Target files and match
        count = 0
        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith(f"l_{self.target_lang}.yml"):
                    base_name = file.replace(f"_l_{self.target_lang}.yml", "")

                    if base_name in english_files:
                        target_data = self._parse_file(os.path.join(root, file))
                        english_data = english_files[base_name]

                        # Match keys
                        for key, target_val in target_data.items():
                            if key in english_data:
                                english_val = english_data[key]
                                # Store in memory: English Val -> Target Val
                                # Only if english val is not empty and long enough to be useful
                                if english_val and len(english_val) > 1:
                                    self.translation_memory[english_val] = target_val
                                    count += 1

        print(f"Loaded {count} vanilla translation entries.")

    def _parse_file(self, path: str) -> dict:
        """
        Parses a YML file and returns { key: value }
        """
        data = {}
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
        except:
            return {}

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("l_"):
                continue

            match = self.entry_pattern.match(line)
            if match:
                key = match.group(1)
                value = match.group(3)
                data[key] = value
        return data

    def get_translation(self, english_text: str) -> str:
        return self.translation_memory.get(english_text)
