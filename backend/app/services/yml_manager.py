import os
import re
import codecs
import tempfile
import subprocess


class YmlManager:
    def __init__(self):
        # Regex to match HOI4 localization format:
        # key: "value"  OR  key:0 "value"
        # Groups: 1=Key, 2=Version (optional), 3=Value, 4=Suffix (comment)
        # We use a non-greedy match for the value? No, value can contain escaped quotes.
        # But for simplicity and robustness against comments:
        # We capture up to the LAST quote as the value end, if possible.
        # Pattern: Start - Key - Ver - " - (Content) - " - (Suffix) - End
        # If content has quotes, they are part of content.
        # We assume the last quote on the line closes the string, UNLESS we see a # comment.
        # Improved Regex: matches standard entries and allows trailing comments
        self.entry_pattern = re.compile(
            r'^\s*([a-zA-Z0-9_\.\-]+)(:\d+)?:?\s*"(.*)"(.*)$'
        )

    def process_file(
        self,
        input_path: str,
        output_path: str,
        translator_func,
        target_lang_header: str,
    ):
        """
        Reads input YML, translates values using translator_func, and writes to output YML.
        translator_func: async function(text) -> text
        """
        try:
            # Enforce UTF-8 BOM reading
            with open(input_path, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Fallback for plain UTF-8 or Latin-1 (rare but possible in old mods)
            try:
                with open(input_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except:
                print(f"Failed to read {input_path} - unknown encoding")
                return

        translated_lines = []
        # Write header (l_korean:)
        translated_lines.append(f"{target_lang_header}:\n")

        # First pass: Identify all translatable lines
        to_translate = []
        indices = []

        for idx, line in enumerate(lines):
            # Skip header line of source
            if idx == 0 and line.strip().startswith("l_"):
                continue

            # Skip empty or comments
            if not line.strip() or line.strip().startswith("#"):
                translated_lines.append(line)
                continue

            match = self.entry_pattern.match(line)
            if match:
                key = match.group(1)
                version = match.group(2) if match.group(2) else ""
                value = match.group(3)
                suffix = match.group(4) if match.group(4) else ""

                to_translate.append((idx, key, version, value, suffix))
            else:
                translated_lines.append(line)

        return to_translate, translated_lines, lines

    @staticmethod
    def write_file(output_path: str, content_lines: list):
        """
        Write file using Python standard IO first, falling back to PowerShell if needed.
        Handles OneDrive synchronization locks more gracefully.
        """
        import shutil

        content = "".join(content_lines)

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Method 1: Direct Python Write (Fastest, works 99%)
        try:
            with open(output_path, "w", encoding="utf-8-sig") as f:
                f.write(content)
            return
        except Exception as e:
            print(f"Direct write failed for {output_path}: {e}. Trying fallback...")

        # Method 2: Write to temp and replace (Atomic-ish)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8-sig", suffix=".yml", delete=False
            ) as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            # Use shutil.move (Python handles OS calls)
            shutil.move(tmp_path, output_path)
            return
        except Exception as e:
            print(f"Shutil move failed: {e}. Trying PowerShell...")
            if "tmp_path" in locals() and os.path.exists(tmp_path):
                pass  # Keep tmp_path for next attempt
            else:
                # Re-create temp if shutil moved it (unlikely on fail) or write failed
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8-sig", suffix=".yml", delete=False
                ) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name

        # Method 3: PowerShell Copy (Handles locked files better than cmd)
        try:
            # Escape single quotes for PowerShell
            ps_tmp = tmp_path.replace("'", "''")
            ps_out = output_path.replace("'", "''")

            cmd = f"powershell -Command \"Copy-Item -Path '{ps_tmp}' -Destination '{ps_out}' -Force\""
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"PowerShell copy failed: {result.stderr}")

            os.remove(tmp_path)
        except Exception as e:
            print(f"All write methods failed for {output_path}: {e}")
            # Try to clean up
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
