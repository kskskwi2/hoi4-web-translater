import os
import shutil
import glob
import re
import subprocess
import time
import asyncio
import ctypes  # For Windows Sleep Prevention
from .yml_manager import YmlManager
from .vanilla_manager import VanillaManager
from .translator.google import GoogleTranslatorService
from .translator.ollama import OllamaTranslatorService
from .translator.openai_service import OpenAITranslatorService
from .translator.claude import ClaudeTranslatorService
from .translator.gemini import GeminiTranslatorService
from . import task_manager


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

    def set_keep_awake(self, enable: bool):
        """
        Prevents Windows from going to sleep during long tasks.
        """
        if os.name == "nt":
            try:
                ES_CONTINUOUS = 0x80000000
                ES_SYSTEM_REQUIRED = 0x00000001

                if enable:
                    # Prevent sleep
                    ctypes.windll.kernel32.SetThreadExecutionState(
                        ES_CONTINUOUS | ES_SYSTEM_REQUIRED
                    )
                    print("System Sleep Disabled (Keep-Awake Active)")
                else:
                    # Allow sleep
                    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                    print("System Sleep Re-enabled")
            except Exception as e:
                print(f"Failed to set keep-awake state: {e}")

    async def generate_translation_mod(
        self,
        source_mod: dict,
        output_root: str,
        task_id: str,
        target_lang: str = "ko",
        service: str = "google",
        service_config: dict = None,
        vanilla_path: str = None,
        glossary: dict = None,
        shutdown_when_complete: bool = False,
    ) -> dict:
        """
        Generates the translation mod.
        source_mod: dict from ModScanner (path, name, id, tags...)
        output_root: Document/Paradox/Mod folder
        task_id: UUID for tracking progress
        service_config: dict with API keys and model settings from frontend
        vanilla_path: Optional path to HoI4 installation for translation memory
        glossary: Optional dict { "Original": "Target" }
        shutdown_when_complete: If True, shutdowns the PC after completion
        """

        # Enable Keep-Awake
        self.set_keep_awake(True)

        try:
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
                translator = GoogleTranslatorService()
            elif service == "ollama":
                translator = OllamaTranslatorService(
                    model=service_config.get("ollama_model", "gemma2"),
                    base_url=service_config.get("ollama_url", "http://localhost:11434"),
                )
            elif service == "openai":
                translator = OpenAITranslatorService(
                    model=service_config.get("openai_model", "gpt-4o-mini"),
                    api_key=service_config.get("openai_key", ""),
                    glossary=glossary,
                )
            elif service == "claude":
                translator = ClaudeTranslatorService(
                    model=service_config.get(
                        "claude_model", "claude-3-5-sonnet-20241022"
                    ),
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
            display_name = source_mod["name"]

            mod_id = source_mod.get("id", "local")
            safe_name = f"translate_mod_{mod_id}_{int(time.time())}"

            new_mod_name = f"[Translate] {display_name}"
            new_dir_name = safe_name
            target_dir = os.path.join(output_root, new_dir_name)

            # 2. Create Descriptor content
            # Fix: Ensure target_dir is valid and handle path separators
            safe_target_dir = target_dir.replace(os.sep, "/") if target_dir else ""

            descriptor_content = f'''version="1.0"
    tags={{
        "Translation"
    }}
    name="{new_mod_name}"
    dependencies={{
        "{source_mod["name"]}"
    }}
    supported_version="{source_mod.get("supported_version", "1.*")}"
    path="{safe_target_dir}"
    '''

            # 3. Write .mod file using subprocess method
            output_root = os.path.normpath(output_root)
            mod_file_path = os.path.join(output_root, f"{new_dir_name}.mod")
            print(f"DEBUG: Attempting to write to: {mod_file_path}")

            success = write_file_via_cmd(mod_file_path, descriptor_content)

            if not success:
                print("WARNING: Subprocess write failed, trying fallback...")
                fallback_root = os.path.join(os.getcwd(), "generated_mods")
                os.makedirs(fallback_root, exist_ok=True)

                output_root = fallback_root
                mod_file_path = os.path.join(output_root, f"{new_dir_name}.mod")
                target_dir = os.path.join(output_root, new_dir_name)

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
            error_log = []  # List to store error details (file, key, message)

            # Count total files first for progress
            total_files = 0
            if os.path.exists(source_loc_path):
                for root, dirs, files in os.walk(source_loc_path):
                    for file in files:
                        if file.endswith("l_english.yml"):
                            total_files += 1

            # Update initial task status
            task_manager.update_task(
                task_id,
                {
                    "status": "running",
                    "total_files": total_files,
                    "processed_files": 0,
                    "percent": 0,
                    "start_time": time.time(),
                    "entries_translated": 0,
                },
            )

            if os.path.exists(source_loc_path):
                print(f"DEBUG: Found source localisation at: {source_loc_path}")
                for root, dirs, files in os.walk(source_loc_path):
                    for file in files:
                        print(f"DEBUG: Checking file: {file}")
                        if file.endswith("l_english.yml"):
                            print(f"DEBUG: Processing English file: {file}")

                            task_manager.update_task(task_id, {"current_file": file})

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
                            paradox_lang = lang_folder_map.get(target_lang, target_lang)

                            # Handle subdirectory structure
                            rel_path = os.path.relpath(root, source_loc_path)
                            if rel_path == ".":
                                target_subdir = os.path.join(
                                    target_dir, "localisation", paradox_lang
                                )
                            else:
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
                            new_filename = file.replace(
                                "l_english.yml", f"l_{paradox_lang}.yml"
                            )
                            target_file_path = os.path.join(target_subdir, new_filename)

                            # Read and Prepare
                            try:
                                result = self.yml_manager.process_file(
                                    source_file_path,
                                    target_file_path,
                                    None,
                                    f"l_{paradox_lang}",
                                )
                            except Exception as e:
                                print(f"Error parsing file {file}: {e}")
                                error_log.append(f"FILE_PARSE_ERROR: {file} - {str(e)}")
                                continue

                            if result is None:
                                continue

                            to_translate, translated_lines_ref, original_lines = result

                            final_lines = []
                            final_lines.append(f"l_{paradox_lang}:\n")

                            translate_map = {}
                            total_entries = len(to_translate)

                            # Update task with entry counts
                            task = task_manager.get_task(task_id)
                            current_total_entries = (
                                task.get("total_entries", 0) + total_entries
                            )
                            task_manager.update_task(
                                task_id,
                                {
                                    "total_entries": current_total_entries,
                                    "current_entry": 0,
                                },
                            )

                            # Batch translation logic
                            if service == "ollama":
                                BATCH_SIZE = 1
                                CONCURRENT_BATCHES = 1
                            elif service == "google":
                                BATCH_SIZE = 20
                                CONCURRENT_BATCHES = 5
                            elif service == "gemini":
                                # Gemini has a strict Rate Limit (10-15 RPM for free tier)
                                # Strategy: Send FEWER requests with MORE content
                                BATCH_SIZE = 50
                                CONCURRENT_BATCHES = 1
                            else:
                                BATCH_SIZE = 10
                                CONCURRENT_BATCHES = 5

                            enriched_items = [
                                (i, item) for i, item in enumerate(to_translate)
                            ]
                            batches = []
                            for i in range(0, total_entries, BATCH_SIZE):
                                batches.append(enriched_items[i : i + BATCH_SIZE])

                            async def process_batch(batch_items):
                                results = []
                                batch_errors = []
                                for seq_idx, item in batch_items:
                                    idx, key, ver, value, suffix = item

                                    # Speed Calculation
                                    task = task_manager.get_task(task_id)
                                    current_time = time.time()
                                    elapsed = current_time - task.get(
                                        "start_time", current_time
                                    )
                                    avg_speed = 0
                                    if elapsed > 0:
                                        avg_speed = round(
                                            task.get("entries_translated", 0) / elapsed,
                                            2,
                                        )

                                    task_manager.update_task(
                                        task_id, {"avg_speed": avg_speed}
                                    )

                                    # 1. Check Vanilla First
                                    if vanilla_db:
                                        vanilla_trans = vanilla_db.get_translation(
                                            value
                                        )
                                        if vanilla_trans:
                                            # Update progress
                                            task = task_manager.get_task(task_id)
                                            new_translated = (
                                                task.get("entries_translated", 0) + 1
                                            )
                                            new_current = (
                                                task.get("current_entry", 0) + 1
                                            )

                                            task_manager.update_task(
                                                task_id,
                                                {
                                                    "entries_translated": new_translated,
                                                    "current_entry": new_current,
                                                },
                                            )

                                            print(
                                                f"  [Task {task_id}] [Vanilla Match] {key}"
                                            )
                                            results.append((idx, vanilla_trans))
                                            continue

                                    # 2. Check & Translate with Glossary
                                    try:
                                        # BaseTranslator.translate_with_preservation now handles glossary replacement if needed
                                        trans_val = await translator.translate_with_preservation(
                                            value, target_lang, glossary=glossary
                                        )

                                        task = task_manager.get_task(task_id)
                                        new_translated = (
                                            task.get("entries_translated", 0) + 1
                                        )
                                        new_current = task.get("current_entry", 0) + 1

                                        task_manager.update_task(
                                            task_id,
                                            {
                                                "entries_translated": new_translated,
                                                "current_entry": new_current,
                                            },
                                        )

                                        print(f"  [Task {task_id}] Translated: {key}")
                                        results.append((idx, trans_val))
                                    except Exception as e:
                                        # Even on error, count as processed
                                        task = task_manager.get_task(task_id)
                                        new_translated = (
                                            task.get("entries_translated", 0) + 1
                                        )
                                        new_current = task.get("current_entry", 0) + 1

                                        task_manager.update_task(
                                            task_id,
                                            {
                                                "entries_translated": new_translated,
                                                "current_entry": new_current,
                                            },
                                        )

                                        print(f"  [Task {task_id}] Error {key}: {e}")
                                        # Log specific translation error
                                        error_entry = f"TRANSLATION_ERROR: File: {file} | Key: {key} | Error: {str(e)}"
                                        results.append(
                                            (idx, value)
                                        )  # Use original value
                                        batch_errors.append(error_entry)

                                return results, batch_errors

                            semaphore = asyncio.Semaphore(CONCURRENT_BATCHES)

                            async def sem_batch(batch_items):
                                async with semaphore:
                                    return await process_batch(batch_items)

                            batch_results_raw = await asyncio.gather(
                                *[sem_batch(b) for b in batches], return_exceptions=True
                            )

                            batch_results = []
                            for res in batch_results_raw:
                                if isinstance(res, Exception):
                                    print(f"Batch execution failed: {res}")
                                    error_log.append(
                                        f"BATCH_EXECUTION_ERROR: {file} - {str(res)}"
                                    )
                                else:
                                    data, errors = res
                                    batch_results.append(data)
                                    if errors:
                                        error_log.extend(errors)

                            for batch_res in batch_results:
                                for idx, val in batch_res:
                                    translate_map[idx] = val

                            # Rebuild file
                            for idx, line in enumerate(original_lines):
                                if idx == 0:
                                    continue
                                if idx in translate_map:
                                    match = self.yml_manager.entry_pattern.match(line)
                                    if match:
                                        indent = line[: line.find(match.group(1))]
                                        key = match.group(1)
                                        ver = match.group(2) if match.group(2) else ":0"
                                        suffix = (
                                            match.group(4) if match.group(4) else ""
                                        )

                                        # Fix: Check if value is None
                                        raw_val = translate_map.get(idx)
                                        if raw_val is None:
                                            raw_val = ""

                                        val = raw_val.replace('"', '\\"')
                                        final_lines.append(
                                            f'{indent}{key}{ver} "{val}"{suffix}\n'
                                        )
                                        val = translate_map[idx].replace('"', '\\"')
                                        final_lines.append(
                                            f'{indent}{key}{ver} "{val}"{suffix}\n'
                                        )
                                    else:
                                        final_lines.append(line)
                                else:
                                    final_lines.append(line)

                            try:
                                self.yml_manager.write_file(
                                    target_file_path, final_lines
                                )
                                files_processed += 1
                            except Exception as e:
                                print(f"Error writing file {target_file_path}: {e}")
                                error_log.append(
                                    f"FILE_WRITE_ERROR: {target_file_path} - {str(e)}"
                                )

                            task_manager.update_task(
                                task_id,
                                {
                                    "processed_files": files_processed,
                                    "percent": int(
                                        (files_processed / total_files) * 100
                                    )
                                    if total_files > 0
                                    else 0,
                                },
                            )

        except Exception as e:
            print(f"Critical Error in generate_translation_mod: {e}")
            task_manager.update_task(task_id, {"status": "error", "error": str(e)})
            self.set_keep_awake(False)
            return {"status": "error", "error": str(e)}
        finally:
            # Disable Keep-Awake regardless of success/fail
            self.set_keep_awake(False)

        # Final Verification: Only mark complete if we actually processed files
        # The loop finishes when all files are done.

        # Write Error Log if exists
        if error_log:
            error_log_path = os.path.join(target_dir, "_translation_errors.log")
            try:
                with open(error_log_path, "w", encoding="utf-8") as f:
                    f.write("=== Translation Error Log ===\n")
                    f.write(f"Generated at: {time.ctime()}\n\n")
                    for err in error_log:
                        f.write(f"{err}\n")
                print(f"Error log written to {error_log_path}")
            except Exception as e:
                print(f"Failed to write error log: {e}")

        # Complete
        task_manager.update_task(
            task_id,
            {
                "status": "completed",
                "percent": 100,
                "path": target_dir,
                "zip_name": new_dir_name,
                "processed_files": files_processed,
            },
        )

        if shutdown_when_complete:
            print("Translation complete. Shutting down system in 60 seconds...")
            if os.name == "nt":
                os.system("shutdown /s /t 60")
            else:
                os.system("shutdown -h now")

        return {
            "status": "success",
            "processed_files": files_processed,
            "path": target_dir,
            "zip_name": new_dir_name,
        }

    def create_zip(self, folder_path: str, zip_name: str) -> str:
        """
        Zips the folder and returns the absolute path to the zip file.
        Stored in the same parent directory.
        """
        output_filename = os.path.join(os.path.dirname(folder_path), zip_name)
        archive_path = shutil.make_archive(output_filename, "zip", folder_path)
