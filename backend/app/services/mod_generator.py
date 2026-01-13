import os
import shutil
import glob
import re
import subprocess
from .yml_manager import YmlManager
from .vanilla_manager import VanillaManager
from .translator.google import GoogleTranslatorService
from .translator.ollama import OllamaTranslatorService
from .translator.openai_service import OpenAITranslatorService
from .translator.claude import ClaudeTranslatorService
from .translator.gemini import GeminiTranslatorService
import asyncio

# Global progress state
translation_progress = {
    "status": "idle",  # idle, running, completed, error
    "current_file": "",
    "processed_files": 0,
    "total_files": 0,
    "percent": 0,
    "current_entry": 0,
    "total_entries": 0,
    "entries_translated": 0,
    "start_time": 0,  # Added for time estimation
    "avg_speed": 0,  # Entries per second
}


def write_file_via_cmd(filepath: str, content: str) -> bool:
    """
    Robust file writing: Direct -> Shutil -> PowerShell.
    Handles Unicode paths and OneDrive locks.
    """
    try:
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Method 1: Direct Write
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Direct write failed for {filepath}: {e}")

        # Prepare temp file
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".tmp", delete=False
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Method 2: Shutil Move
        try:
            shutil.move(tmp_path, filepath)
            return True
        except Exception as e:
            print(f"Shutil move failed: {e}")

        # Method 3: PowerShell
        try:
            # Escape single quotes
            ps_tmp = tmp_path.replace("'", "''")
            ps_dest = filepath.replace("'", "''")

            # Create directory via PS just in case
            ps_dir = os.path.dirname(filepath).replace("'", "''")
            subprocess.run(
                f"powershell -Command \"New-Item -ItemType Directory -Path '{ps_dir}' -Force -ErrorAction SilentlyContinue\"",
                shell=True,
                capture_output=True,
            )

            copy_cmd = f"powershell -Command \"Copy-Item -Path '{ps_tmp}' -Destination '{ps_dest}' -Force\""
            result = subprocess.run(
                copy_cmd, shell=True, capture_output=True, text=True
            )

            if os.path.exists(tmp_path):
                os.remove(tmp_path)

            if result.returncode == 0:
                return True
            else:
                print(f"PowerShell copy failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"PowerShell method failed: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False

    except Exception as e:
        print(f"write_file_via_cmd fatal error: {e}")
        return False


class ModGenerator:
    def __init__(self):
        self.yml_manager = YmlManager()

    async def generate_translation_mod(
        self,
        source_mod: dict,
        output_root: str,
        target_lang: str = "ko",
        service: str = "google",
        service_config: dict = None,
        vanilla_path: str = None,
        glossary: dict = None,  # Added
    ) -> dict:
        """
        Generates the translation mod.
        source_mod: dict from ModScanner (path, name, id, tags...)
        output_root: Document/Paradox/Mod folder
        service_config: dict with API keys and model settings from frontend
        vanilla_path: Optional path to HoI4 installation for translation memory
        glossary: Optional dict { "Original": "Target" }
        """

        if service_config is None:
            service_config = {}

        # Initialize Vanilla Manager if path provided
        vanilla_db = None
        if vanilla_path:
            try:
                vm = VanillaManager(vanilla_path, target_lang)
                vm.load_database()
                vanilla_db = vm
            except Exception as e:
                print(f"Failed to initialize VanillaManager: {e}")

        # Service Selection with config
        if service == "google":
            translator = GoogleTranslatorService()  # Google doesn't support system prompt easily, we rely on post-processing or manual injection
        elif service == "ollama":
            translator = OllamaTranslatorService(
                model=service_config.get("ollama_model", "gemma2"),
                base_url=service_config.get("ollama_url", "http://localhost:11434"),
            )
        elif service == "openai":
            translator = OpenAITranslatorService(
                model=service_config.get("openai_model", "gpt-4o-mini"),
                api_key=service_config.get("openai_key", ""),
                glossary=glossary,  # Pass glossary to service
            )
        elif service == "claude":
            translator = ClaudeTranslatorService(
                model=service_config.get("claude_model", "claude-3-5-sonnet-20241022"),
                api_key=service_config.get("claude_key", ""),
                glossary=glossary,
            )
        elif service == "gemini":
            translator = GeminiTranslatorService(
                model=service_config.get("gemini_model", "gemini-1.5-flash"),
                api_key=service_config.get("gemini_key", ""),
                glossary=glossary,
            )
        else:
            translator = GoogleTranslatorService()

        # 1. Define new mod metadata
        # Display name (can contain unicode)
        display_name = source_mod["name"]

        # Filesystem name: USE ID for safety to avoid ANY invalid char issues
        # OneDrive/Windows can be picky about certain chars or length
        import time

        mod_id = source_mod.get("id", "local")
        safe_name = f"translate_mod_{mod_id}_{int(time.time())}"

        new_mod_name = f"[Translate] {display_name}"
        new_dir_name = safe_name  # Folder name matches mod file base name
        target_dir = os.path.join(output_root, new_dir_name)

        # ... (Rest is same) ...

        # 2. Create Descriptor content
        # Dependencies is crucial for translation mods to load AFTER the original
        descriptor_content = f'''version="1.0"
tags={{
    "Translation"
}}
name="{new_mod_name}"
dependencies={{
    "{source_mod["name"]}"
}}
supported_version="{source_mod.get("supported_version", "1.*")}"
path="{target_dir.replace(os.sep, "/")}"
'''

        # 3. Write .mod file using subprocess method
        output_root = os.path.normpath(output_root)

        mod_file_path = os.path.join(output_root, f"{new_dir_name}.mod")
        print(f"DEBUG: Attempting to write to: {mod_file_path}")

        # Use subprocess-based write
        success = write_file_via_cmd(mod_file_path, descriptor_content)

        if not success:
            print("WARNING: Subprocess write failed, trying fallback...")
            # Fallback to local directory
            fallback_root = os.path.join(os.getcwd(), "generated_mods")
            os.makedirs(fallback_root, exist_ok=True)

            output_root = fallback_root
            mod_file_path = os.path.join(output_root, f"{new_dir_name}.mod")
            target_dir = os.path.join(output_root, new_dir_name)

            # Update descriptor path
            descriptor_content = f'''version="1.0"
tags={{
    "Translation"
}}
name="{new_mod_name}"
dependencies={{
    "{source_mod["name"]}"
}}
supported_version="{source_mod.get("supported_version", "1.*")}"
path="{target_dir.replace(os.sep, "/")}"
'''
            with open(mod_file_path, "w", encoding="utf-8") as f:
                f.write(descriptor_content)
            print(f"SUCCESS: Wrote to fallback: {mod_file_path}")
        else:
            print(f"SUCCESS: Wrote mod file via subprocess: {mod_file_path}")

        # 4. Create directory structure
        target_dir = os.path.join(output_root, new_dir_name)
        subprocess.run(
            f'mkdir "{os.path.join(target_dir, "localisation", "replace")}"',
            shell=True,
            capture_output=True,
        )

        # Write descriptor.mod inside the mod folder (NO PATH LINE)
        descriptor_internal = f'''version="1.0"
tags={{
    "Translation"
}}
name="{new_mod_name}"
dependencies={{
    "{source_mod["name"]}"
}}
supported_version="{source_mod.get("supported_version", "1.*")}"
'''
        write_file_via_cmd(
            os.path.join(target_dir, "descriptor.mod"), descriptor_internal
        )

        # Process Thumbnail
        from .thumbnail_processor import process_thumbnail

        process_thumbnail(source_mod["path"], target_dir, text="Korean Translation")

        # 5. Process Localisation Files
        source_loc_path = os.path.join(source_mod["path"], "localisation")
        files_processed = 0

        # Count total files first for progress
        total_files = 0
        if os.path.exists(source_loc_path):
            for root, dirs, files in os.walk(source_loc_path):
                for file in files:
                    if file.endswith("l_english.yml"):
                        total_files += 1

        # Update global progress
        global translation_progress
        import time

        translation_progress["status"] = "running"
        translation_progress["total_files"] = total_files
        translation_progress["processed_files"] = 0
        translation_progress["percent"] = 0
        translation_progress["start_time"] = time.time()
        translation_progress["entries_translated"] = 0

        if os.path.exists(source_loc_path):
            print(f"DEBUG: Found source localisation at: {source_loc_path}")
            for root, dirs, files in os.walk(source_loc_path):
                for file in files:
                    print(f"DEBUG: Checking file: {file}")
                    if file.endswith("l_english.yml"):
                        print(f"DEBUG: Processing English file: {file}")
                        # Update progress
                        translation_progress["current_file"] = file

                        # Map language codes to HoI4 folder names
                        lang_folder_map = {
                            "ko": "korean",
                            "en": "english",
                            "fr": "french",
                            "de": "german",
                            "es": "spanish",
                            "pt": "braz_por",
                            "pl": "polish",
                            "ru": "russian",
                            "ja": "japanese",
                            "zh": "simp_chinese",
                        }
                        # Paradox uses full names for folders and file suffixes
                        paradox_lang = lang_folder_map.get(target_lang, target_lang)

                        # Handle subdirectory structure
                        rel_path = os.path.relpath(root, source_loc_path)

                        # Calculate target subdirectory
                        # If we are at root of localisation, put in language folder
                        if rel_path == ".":
                            target_subdir = os.path.join(
                                target_dir, "localisation", paradox_lang
                            )
                        else:
                            # Replace 'english' in path with target language if present
                            rel_path_parts = rel_path.split(os.sep)
                            new_rel_path_parts = []
                            for part in rel_path_parts:
                                if part.lower() == "english":
                                    new_rel_path_parts.append(paradox_lang)
                                else:
                                    new_rel_path_parts.append(part)

                            rel_path_target = os.path.join(*new_rel_path_parts)
                            target_subdir = os.path.join(
                                target_dir, "localisation", rel_path_target
                            )

                        os.makedirs(target_subdir, exist_ok=True)

                        source_file_path = os.path.join(root, file)
                        # File MUST end with _l_language.yml
                        new_filename = file.replace(
                            "l_english.yml", f"l_{paradox_lang}.yml"
                        )
                        target_file_path = os.path.join(target_subdir, new_filename)

                        # Read and Prepare
                        # Header MUST be l_language:
                        result = self.yml_manager.process_file(
                            source_file_path,
                            target_file_path,
                            None,
                            f"l_{paradox_lang}",
                        )

                        if result is None:
                            print(f"DEBUG: process_file returned None for {file}")
                            continue

                        to_translate, translated_lines_ref, original_lines = result
                        print(
                            f"DEBUG: Found {len(to_translate)} entries to translate in {file}"
                        )

                        final_lines = []
                        # Header MUST be l_language:
                        final_lines.append(f"l_{paradox_lang}:\n")

                        translate_map = {}
                        total_entries = len(to_translate)
                        translation_progress["total_entries"] = total_entries
                        translation_progress["current_entry"] = 0

                        # Batch translation logic
                        # Increase batch sizes for cloud APIs since we'll process concurrently
                        if service == "ollama":
                            BATCH_SIZE = 1
                            CONCURRENT_BATCHES = 1
                        elif service == "google":
                            BATCH_SIZE = 20
                            CONCURRENT_BATCHES = 5
                        else:
                            BATCH_SIZE = 10
                            CONCURRENT_BATCHES = 5

                        # Create batches with sequential index
                        enriched_items = [
                            (i, item) for i, item in enumerate(to_translate)
                        ]
                        batches = []
                        for i in range(0, total_entries, BATCH_SIZE):
                            batches.append(enriched_items[i : i + BATCH_SIZE])

                        # Define batch processor
                        async def process_batch(batch_items):
                            results = []
                            for seq_idx, item in batch_items:
                                idx, key, ver, value, suffix = item

                                # Dynamic Speed Calculation
                                current_time = time.time()
                                elapsed = current_time - translation_progress.get(
                                    "start_time", current_time
                                )
                                if elapsed > 0:
                                    translation_progress["avg_speed"] = round(
                                        translation_progress["entries_translated"]
                                        / elapsed,
                                        2,
                                    )

                                # 1. Check Vanilla First
                                if vanilla_db:
                                    vanilla_trans = vanilla_db.get_translation(value)
                                    if vanilla_trans:
                                        # Progress update logic moved inside loop for real-time feedback
                                        translation_progress["entries_translated"] += 1
                                        translation_progress["current_entry"] += 1

                                        current_num = translation_progress[
                                            "current_entry"
                                        ]
                                        percent = int(
                                            (current_num / total_entries) * 100
                                        )
                                        print(
                                            f"  [Progress {percent}%] ({current_num}/{total_entries}) [Vanilla Match] {key} -> {vanilla_trans[:30]}..."
                                        )

                                        results.append((idx, vanilla_trans))
                                        continue

                                # 2. Check Glossary
                                try:
                                    trans_val = (
                                        await translator.translate_with_preservation(
                                            value, target_lang
                                        )
                                    )

                                    # 3. Post-process Glossary
                                    if glossary:
                                        pass

                                    # Update global progress immediately
                                    translation_progress["entries_translated"] += 1
                                    translation_progress["current_entry"] += 1

                                    current_num = translation_progress["current_entry"]
                                    percent = int((current_num / total_entries) * 100)
                                    print(
                                        f"  [Progress {percent}%] ({current_num}/{total_entries}) Translated: {key}"
                                    )
                                    results.append((idx, trans_val))
                                except Exception as e:
                                    # Even on error, we count as processed
                                    translation_progress["entries_translated"] += 1
                                    translation_progress["current_entry"] += 1

                                    current_num = translation_progress["current_entry"]
                                    percent = int((current_num / total_entries) * 100)
                                    print(
                                        f"  [Progress {percent}%] ({current_num}/{total_entries}) Error {key}: {e}"
                                    )
                                    results.append((idx, value))

                                # Calculate speed
                                current_time = time.time()
                                elapsed = current_time - translation_progress.get(
                                    "start_time", current_time
                                )
                                if elapsed > 0:
                                    translation_progress["avg_speed"] = (
                                        translation_progress["entries_translated"]
                                        / elapsed
                                    )

                            return results

                        # Process batches with semaphore for concurrency control
                        semaphore = asyncio.Semaphore(CONCURRENT_BATCHES)

                        async def sem_batch(batch_items):
                            async with semaphore:
                                return await process_batch(batch_items)

                        # Execute all batches
                        batch_results = await asyncio.gather(
                            *[sem_batch(b) for b in batches]
                        )

                        # Flatten results (Progress already updated)
                        for batch_res in batch_results:
                            for idx, val in batch_res:
                                translate_map[idx] = val

                        # Rebuild file content
                        for idx, line in enumerate(original_lines):
                            if idx == 0:
                                continue

                            if idx in translate_map:
                                match = self.yml_manager.entry_pattern.match(line)
                                if match:
                                    indent = line[: line.find(match.group(1))]
                                    key = match.group(1)
                                    # Ensure version is :0 if missing or whatever it was (usually :0)
                                    # If original had :10, keep it. If none, add :0
                                    ver = match.group(2) if match.group(2) else ":0"
                                    suffix = match.group(4) if match.group(4) else ""
                                    val = translate_map[idx]
                                    val = val.replace('"', '\\"')
                                    # Append suffix (comment) back
                                    new_line = f'{indent}{key}{ver} "{val}"{suffix}\n'
                                    final_lines.append(new_line)
                                else:
                                    final_lines.append(line)
                            else:
                                final_lines.append(line)

                        self.yml_manager.write_file(target_file_path, final_lines)
                        files_processed += 1

                        # Update progress
                        translation_progress["processed_files"] = files_processed
                        translation_progress["percent"] = (
                            int((files_processed / total_files) * 100)
                            if total_files > 0
                            else 100
                        )

        translation_progress["status"] = "completed"
        translation_progress["percent"] = 100
        # Store result in progress for polling frontend
        translation_progress["path"] = target_dir
        translation_progress["zip_name"] = new_dir_name

        return {
            "status": "success",
            "processed_files": files_processed,
            "path": target_dir,
            "zip_name": new_dir_name,  # Used for zipping
        }

    def create_zip(self, folder_path: str, zip_name: str) -> str:
        """
        Zips the folder and returns the absolute path to the zip file.
        Stored in the same parent directory.
        """
        # output_filename should not have extension, make_archive adds .zip
        output_filename = os.path.join(os.path.dirname(folder_path), zip_name)
        archive_path = shutil.make_archive(output_filename, "zip", folder_path)
        return archive_path
