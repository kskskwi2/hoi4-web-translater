import httpx
import os
import aiofiles
from typing import List, Dict, Optional, Any


class ParaTranzClient:
    """
    Client for interacting with the ParaTranz API.
    Docs: https://paratranz.apifox.cn/
    """

    BASE_URL = "https://paratranz.cn/api"

    def __init__(self, token: str):
        self.token = token
        self.headers = {"Authorization": self.token}

    async def get_projects(self) -> List[Dict]:
        """List all projects user has access to (paginated)."""
        all_projects = []
        page = 1
        page_size = 800

        async with httpx.AsyncClient() as client:
            while True:
                resp = await client.get(
                    f"{self.BASE_URL}/projects",
                    headers=self.headers,
                    params={"page": page, "pageSize": page_size},
                )
                resp.raise_for_status()
                data = resp.json()

                results = []
                if isinstance(data, dict) and "results" in data:
                    results = data["results"]
                elif isinstance(data, list):
                    results = data
                else:
                    break

                all_projects.extend(results)

                if isinstance(data, dict):
                    page_count = data.get("pageCount", 1)
                    if page >= page_count:
                        break
                else:
                    if len(results) < page_size:
                        break

                page += 1

        return all_projects

    async def create_project(
        self, name: str, source_lang: str, target_lang: str, description: str = ""
    ) -> Dict:
        """Create a new project."""
        payload = {
            "name": name,
            "source": source_lang,
            "target": target_lang,
            "description": description,
            "public": False,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/projects", headers=self.headers, json=payload
            )
            resp.raise_for_status()
            return resp.json()

    async def get_files(self, project_id: int) -> List[Dict]:
        """List files in a project."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/projects/{project_id}/files", headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()

    async def create_file(
        self, project_id: int, file_path: str, remote_path: str = ""
    ) -> Dict:
        """
        Create a NEW file (Source) in ParaTranz.
        Endpoint: POST /projects/{projectId}/files
        Body: file=@...
        """
        return await self._do_upload(project_id, file_path, remote_path)

    async def update_source_file(
        self, project_id: int, file_id: int, file_path: str
    ) -> Dict:
        """
        Update an EXISTING Source file content.
        Endpoint: POST /projects/{projectId}/files/{fileId}
        Body: file=@..., type="update" (or default)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)

        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f, "application/octet-stream")}
                data = {"type": "update"}  # Explicitly 'update'

                print(f"Updating source file {file_name} (ID: {file_id})")
                resp = await client.post(
                    f"{self.BASE_URL}/projects/{project_id}/files/{file_id}",
                    headers=self.headers,
                    data=data,
                    files=files,
                    timeout=60.0,
                )
                resp.raise_for_status()
                return resp.json()

    async def import_translation_data(
        self, project_id: int, file_id: int, file_path: str
    ) -> Dict:
        """
        Import TRANSLATION data into an existing Source file.
        Endpoint: POST /projects/{projectId}/files/{fileId}
        Body: file=@..., type="import" (CRITICAL)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)

        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f, "application/octet-stream")}
                data = {"type": "import"}  # CRITICAL: 'import' means translation data

                print(f"Importing translation {file_name} for file ID {file_id}")
                resp = await client.post(
                    f"{self.BASE_URL}/projects/{project_id}/files/{file_id}",
                    headers=self.headers,
                    data=data,
                    files=files,
                    timeout=60.0,
                )

                if resp.status_code == 422:
                    print(f"Error 422 importing translation: {resp.text}")

                resp.raise_for_status()
                return resp.json()

    async def _do_upload(
        self, project_id: int, file_path: str, remote_path: str = ""
    ) -> Dict:
        """Internal helper for creating new files."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)

        if remote_path.startswith("/"):
            remote_path = remote_path[1:]

        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f, "application/octet-stream")}
                data = {}
                if remote_path and remote_path != ".":
                    data["path"] = remote_path

                print(f"Creating new source file {file_name} in project {project_id}")
                resp = await client.post(
                    f"{self.BASE_URL}/projects/{project_id}/files",
                    headers=self.headers,
                    data=data,
                    files=files,
                    timeout=60.0,
                )

                if resp.status_code == 422:
                    print(f"Error 422: {resp.text}")

                if resp.status_code == 409:
                    print(
                        f"File {file_name} exists. Caller should have used update_source_file."
                    )

                resp.raise_for_status()
                return resp.json()

    async def create_artifact(self, project_id: int) -> Dict:
        """Trigger a build to generate translated files."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/projects/{project_id}/artifacts", headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()

    async def get_artifacts(self, project_id: int) -> List[Dict]:
        """Get list of build artifacts."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/projects/{project_id}/artifacts", headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()

    async def download_artifact(self, url: str, dest_path: str):
        """Download artifact zip file."""
        target_url = url if url.startswith("http") else f"https://paratranz.cn{url}"
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", target_url, headers=self.headers) as resp:
                resp.raise_for_status()
                with open(dest_path, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        f.write(chunk)
