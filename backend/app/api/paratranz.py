from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header, Depends
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
import zipfile
from sqlalchemy.orm import Session
from ..services.paratranz_wrapper import ParaTranzSDKWrapper
from ..services.mod_scanner import ModScanner
from ..database import get_db
from ..models import Settings

router = APIRouter()


class CreateProjectRequest(BaseModel):
    name: str
    source_lang: str = "en"
    target_lang: str = "ko"
    description: Optional[str] = ""


class UploadModRequest(BaseModel):
    project_id: Optional[int] = None
    mod_path: str
    translation_path: Optional[str] = None  # Path to the generated translation mod


# In-memory storage for token (simple session-like behavior for single user app)
# Ideally, passed from frontend every time
# We will require Authorization header in requests


def get_client(authorization: str = Header(None)) -> ParaTranzSDKWrapper:
    if not authorization:
        raise HTTPException(
            status_code=401, detail="Missing Authorization header (ParaTranz Token)"
        )
    return ParaTranzSDKWrapper(authorization)


# Language Code to Paradox Folder Name Mapping (Same as ModGenerator)
LANG_FOLDER_MAP = {
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
    "zh-CN": "simp_chinese",
    "zh-TW": "simp_chinese",
}


@router.get("/projects")
async def list_projects(authorization: str = Header(None)):
    """List ParaTranz projects."""
    client = get_client(authorization)
    try:
        return await client.get_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects")
async def create_project(
    request: CreateProjectRequest, authorization: str = Header(None)
):
    """Create a new ParaTranz project."""
    client = get_client(authorization)
    try:
        return await client.create_project(
            request.name, request.source_lang, request.target_lang, request.description
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_mod_files(
    request: UploadModRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """
    Two-step upload process:
    1. Upload Source Files (e.g. l_english.yml) from original mod.
    2. Import Translation Files (e.g. l_korean.yml) from generated mod.
    """
    client = get_client(authorization)

    # 1. Handle Project ID & Settings (Request Body -> DB Settings)
    project_id = request.project_id

    settings = db.query(Settings).first()
    if not settings:
        raise HTTPException(status_code=400, detail="Settings not found")

    if not project_id:
        if settings and settings.paratranz_project_id:
            project_id = settings.paratranz_project_id
        else:
            raise HTTPException(
                status_code=400,
                detail="Project ID not provided and not found in settings",
            )

    # Determine Source and Target Suffixes
    source_code = settings.source_language or "en"
    target_code = settings.target_language or "ko"

    source_pdx = LANG_FOLDER_MAP.get(source_code, source_code)
    target_pdx = LANG_FOLDER_MAP.get(target_code, target_code)

    source_suffix = f"l_{source_pdx}"
    target_suffix = f"l_{target_pdx}"

    print(f"DEBUG: Matching {target_suffix} -> {source_suffix} for upload linking")

    mod_path = request.mod_path
    trans_path = request.translation_path

    if not os.path.exists(mod_path):
        raise HTTPException(status_code=404, detail="Mod path not found")

    uploaded_files = []
    errors = []

    # --- Step 0: Fetch existing files to handle updates ---
    existing_files_map = {}  # full_path -> id
    source_file_map = {}  # full_path -> id (for linking translations)

    try:
        existing_files = await client.get_files(project_id)
        for f in existing_files:
            if not isinstance(f, dict):
                continue

            f_id = f.get("id")
            f_name = f.get("name")
            if not f_id or not f_name:
                continue

            f_path = f.get("path", "").replace("\\", "/")
            if f_path.startswith("/"):
                f_path = f_path[1:]

            # Ensure no double slashes
            if f_path:
                if f_path.endswith("/"):
                    full_path = f"{f_path}{f_name}"
                else:
                    full_path = f"{f_path}/{f_name}"
            else:
                full_path = f_name

            print(f"DEBUG: Mapped existing file: {full_path} (ID: {f_id})")
            existing_files_map[full_path] = f_id
            source_file_map[full_path] = f_id
    except Exception as e:
        print(f"Failed to fetch existing files: {e}")
        # Continue anyway, will attempt to create new files

    # --- Step 1: Upload Source Files ---
    source_loc_path = os.path.join(mod_path, "localisation")
    if not os.path.exists(source_loc_path):
        raise HTTPException(
            status_code=400, detail="No localisation folder found in source mod"
        )

    for root, dirs, files in os.walk(source_loc_path):
        for file in files:
            if file.endswith("l_english.yml"):
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, source_loc_path)
                remote_path = rel_path.replace("\\", "/")
                if remote_path == ".":
                    remote_path = ""

                full_rel_path = f"{remote_path}/{file}" if remote_path else file

                try:
                    if full_rel_path in existing_files_map:
                        file_id = existing_files_map[full_rel_path]
                        print(f"Updating existing file {full_rel_path} (ID: {file_id})")
                        res = await client.update_file(project_id, file_id, abs_path)
                        status = "source_updated"
                    else:
                        print(f"Uploading new file {full_rel_path}")
                        res = await client.create_file(
                            project_id, abs_path, remote_path
                        )
                        status = "source_created"

                    # Extract ID from response (robust handling)
                    file_data = res.get("file", res) if isinstance(res, dict) else res
                    new_id = getattr(file_data, "id", None) or file_data.get("id")

                    if new_id:
                        # CRITICAL FIX: Ensure map is updated with standardized path
                        std_path = full_rel_path.replace("\\", "/")
                        if std_path.startswith("/"):
                            std_path = std_path[1:]

                        source_file_map[std_path] = new_id
                        # Also add basename for fuzzy matching fallback
                        source_file_map[os.path.basename(std_path)] = new_id

                        print(f"DEBUG: Source file map updated: {std_path} -> {new_id}")

                        uploaded_files.append(
                            {
                                "file": file,
                                "remote_path": remote_path,
                                "status": status,
                                "id": new_id,
                            }
                        )
                except Exception as e:
                    errors.append({"file": file, "error": str(e)})

    # --- Step 2: Import Translation Files (if provided) ---
    if trans_path and os.path.exists(trans_path):
        trans_loc_path = os.path.join(trans_path, "localisation")
        if os.path.exists(trans_loc_path):
            for root, dirs, files in os.walk(trans_loc_path):
                for file in files:
                    # Check for translation files (e.g. l_korean.yml)
                    if not file.endswith("l_english.yml") and file.endswith(".yml"):
                        abs_path = os.path.join(root, file)
                        rel_path = os.path.relpath(root, trans_loc_path)
                        remote_path = rel_path.replace("\\", "/")
                        if remote_path == ".":
                            remote_path = ""

                        # Find corresponding source file ID
                        # Dynamic Heuristic: Replace target language suffix with source language suffix
                        source_filename = file
                        if target_suffix in file:
                            source_filename = file.replace(target_suffix, source_suffix)

                        # 1. Try Exact Path Match (assuming folder structure mirrors source)
                        # e.g. localisation/english/file_l_english.yml vs localisation/korean/file_l_korean.yml
                        # We need to swap the language directory name too if present.

                        target_lang_folder = LANG_FOLDER_MAP.get(
                            target_code, target_code
                        )
                        source_lang_folder = LANG_FOLDER_MAP.get(
                            source_code, source_code
                        )

                        adjusted_remote_path = remote_path
                        if target_lang_folder in adjusted_remote_path:
                            adjusted_remote_path = adjusted_remote_path.replace(
                                target_lang_folder, source_lang_folder
                            )

                        if adjusted_remote_path:
                            possible_source_key = (
                                f"{adjusted_remote_path}/{source_filename}"
                            )
                        else:
                            possible_source_key = source_filename

                        matched_id = source_file_map.get(possible_source_key)

                        if matched_id:
                            print(
                                f"DEBUG: Exact match found: {possible_source_key} -> ID {matched_id}"
                            )

                        # 2. Try Fuzzy Match by Filename (Ignore Path)
                        # This is CRITICAL because modders often change folder structures or put translations in separate folders.
                        if not matched_id:
                            print(
                                f"DEBUG: Exact match failed for {possible_source_key}. Trying fuzzy filename match..."
                            )
                            # Iterate all source files and check if filename matches source_filename
                            # Prefer 'english/' folder if multiple matches exist
                            candidates = []
                            for src_path, src_id in source_file_map.items():
                                src_basename = os.path.basename(src_path)
                                if src_basename == source_filename:
                                    candidates.append((src_path, src_id))

                            if candidates:
                                # Heuristic: Pick the one that looks most like a standard path (e.g. contains 'english')
                                best_match = candidates[0]  # Default to first
                                for cand in candidates:
                                    if f"/{source_lang_folder}/" in cand[0] or cand[
                                        0
                                    ].startswith(f"{source_lang_folder}/"):
                                        best_match = cand
                                        break

                                matched_id = best_match[1]
                                print(
                                    f"DEBUG: Fuzzy matched {best_match[0]} (ID: {matched_id}) for {file}"
                                )

                        if matched_id:
                            try:
                                # Use explicit import_translation_data
                                await client.save_file_translation(
                                    project_id, matched_id, abs_path
                                )
                                uploaded_files.append(
                                    {
                                        "file": file,
                                        "remote_path": remote_path,
                                        "status": "translation_imported",
                                        "linked_to": matched_id,
                                    }
                                )
                            except Exception as e:
                                print(f"Failed to import translation {file}: {e}")
                                errors.append(
                                    {
                                        "file": file,
                                        "error": f"Import failed: {str(e)}",
                                    }
                                )
                        else:
                            print(f"No matching source file found for {file}")
                            errors.append(
                                {
                                    "file": file,
                                    "error": "No matching source file found on ParaTranz",
                                }
                            )

    return {"uploaded": uploaded_files, "errors": errors}


@router.post("/download/{project_id}")
async def download_and_apply(
    project_id: int, target_mod_path: str, authorization: str = Header(None)
):
    """
    Trigger build, download artifact, and apply to a local mod folder.
    This effectively "Imports" translations from ParaTranz to local.
    """
    client = get_client(authorization)

    try:
        # 1. Trigger Build
        print(f"Triggering build for project {project_id}...")
        await client.create_artifact(project_id)

        # 2. Get Artifacts
        artifacts = await client.get_artifacts(project_id)
        if not artifacts:
            raise HTTPException(
                status_code=404, detail="No artifacts found after build."
            )

        # Get latest
        latest_artifact = artifacts[0]  # Usually sorted by date desc?
        download_url = latest_artifact.get("url")

        # 3. Download Zip
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = tmp.name

        print(f"Downloading artifact from {download_url}...")
        await client.download_artifact(download_url, tmp_path)

        # 4. Extract and Apply
        # We'll extract to a temp dir first
        extract_dir = os.path.join(tempfile.gettempdir(), f"pt_extract_{project_id}")
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(tmp_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # 5. Move files to target
        target_loc_path = os.path.join(target_mod_path, "localisation")
        os.makedirs(target_loc_path, exist_ok=True)

        count = 0
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, extract_dir)
                dest_file = os.path.join(target_loc_path, rel_path)

                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(src_file, dest_file)
                count += 1

        # Cleanup
        os.remove(tmp_path)
        shutil.rmtree(extract_dir)

        return {"status": "success", "files_synced": count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
