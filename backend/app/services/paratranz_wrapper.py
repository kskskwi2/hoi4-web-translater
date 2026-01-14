import sys
import os
import asyncio
import traceback
import httpx
from typing import List, Optional, Dict, Any

# Add SDK to path
# Use relative path for portability
SDK_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "paratranz-sdk",
)

if os.path.exists(SDK_PATH) and SDK_PATH not in sys.path:
    sys.path.append(SDK_PATH)
else:
    # Fallback to local 'paratranz-sdk' in backend or root
    SDK_PATH_ALT = os.path.join(os.getcwd(), "paratranz-sdk")
    if os.path.exists(SDK_PATH_ALT) and SDK_PATH_ALT not in sys.path:
        sys.path.append(SDK_PATH_ALT)

try:
    import paratranz_client
    from paratranz_client.rest import ApiException
    from paratranz_client.models import File as PTFile
except ImportError:
    print(
        "WARNING: ParaTranz SDK not found. Please ensure it is in C:\\자동번역\\paratranz-sdk"
    )
    paratranz_client = None


class ParaTranzSDKWrapper:
    def __init__(self, token: str):
        # Strip whitespace from token just in case
        self.token = token.strip() if token else ""
        self.base_url = "https://paratranz.cn/api"
        self.headers = {"Authorization": self.token}

        if paratranz_client:
            self.configuration = paratranz_client.Configuration(host=self.base_url)
            self.configuration.api_key["Token"] = self.token
        else:
            self.configuration = None

    async def get_projects(self):
        """
        Manually implement get_projects because the generated SDK
        expects a List but the API returns a Dict with 'results'.
        """
        all_projects = []
        page = 1
        page_size = 800

        try:
            async with httpx.AsyncClient() as client:
                while True:
                    print(f"DEBUG: Calling {self.base_url}/projects page {page}")
                    resp = await client.get(
                        f"{self.base_url}/projects",
                        headers=self.headers,
                        params={"page": page, "pageSize": page_size},
                        timeout=30.0,
                    )

                    if resp.status_code != 200:
                        print(f"DEBUG: API Error {resp.status_code}: {resp.text}")

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
        except Exception as e:
            print(f"Error in get_projects (Manual): {e}")
            traceback.print_exc()
            raise e

    async def create_project(
        self, name: str, source_lang: str, target_lang: str, description: str = ""
    ):
        try:
            async with paratranz_client.ApiClient(self.configuration) as api_client:
                api_instance = paratranz_client.ProjectsApi(api_client)

                project_model = paratranz_client.models.Project(
                    name=name,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    description=description,
                )

                response = await api_instance.create_project(project=project_model)
                return response.to_dict() if hasattr(response, "to_dict") else response
        except Exception as e:
            print(f"Error in create_project: {e}")
            traceback.print_exc()
            raise e

    async def get_files(self, project_id: int) -> List[dict]:
        """
        Manually fetch files to ensure we get the 'path' property,
        which might be missing in the generated SDK model.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/projects/{project_id}/files",
                    headers=self.headers,
                    timeout=30.0,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            print(f"Error in get_files (Manual): {e}")
            traceback.print_exc()
            raise e

    async def create_file(self, project_id: int, file_path: str, remote_path: str):
        return await self._manual_upload(project_id, file_path, remote_path)

    async def _manual_upload(
        self, project_id: int, file_path: str, remote_path: str = ""
    ):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        if remote_path.startswith("/"):
            remote_path = remote_path[1:]

        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                # Prepare file and data
                files = {"file": (file_name, f, "application/octet-stream")}
                data = {}
                if remote_path and remote_path != ".":
                    data["path"] = remote_path

                resp = await client.post(
                    f"{self.base_url}/projects/{project_id}/files",
                    headers=self.headers,
                    data=data,
                    files=files,
                    timeout=60.0,
                )
                resp.raise_for_status()
                return resp.json()

    async def update_file(self, project_id: int, file_id: int, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f, "application/octet-stream")}
                data = {"type": "update"}

                resp = await client.post(
                    f"{self.base_url}/projects/{project_id}/files/{file_id}",
                    headers=self.headers,
                    data=data,
                    files=files,
                    timeout=60.0,
                )
                resp.raise_for_status()
                return resp.json()

    async def save_file_translation(
        self, project_id: int, file_id: int, file_path: str
    ):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                # The endpoint expects 'file' in multipart/form-data
                files = {"file": (file_name, f, "application/octet-stream")}

                # IMPORTANT: Endpoint is /projects/{pid}/files/{fid}/translation
                # This ensures it's treated as Translation Import, not File Replacement.
                resp = await client.post(
                    f"{self.base_url}/projects/{project_id}/files/{file_id}/translation",
                    headers=self.headers,
                    files=files,
                    timeout=60.0,
                )

                if resp.status_code != 200:
                    print(
                        f"DEBUG: Translation Import Failed {resp.status_code}: {resp.text}"
                    )

                resp.raise_for_status()
                return resp.json()

    async def create_artifact(self, project_id: int):
        try:
            async with paratranz_client.ApiClient(self.configuration) as api_client:
                api_instance = paratranz_client.ArtifactsApi(api_client)
                response = await api_instance.generate_artifact(project_id)
                return response.to_dict() if hasattr(response, "to_dict") else response
        except Exception as e:
            print(f"Error in create_artifact: {e}")
            traceback.print_exc()
            raise e

    async def get_artifacts(self, project_id: int):
        try:
            async with paratranz_client.ApiClient(self.configuration) as api_client:
                api_instance = paratranz_client.ArtifactsApi(api_client)
                res = await api_instance.get_artifact(project_id)
                return [r.to_dict() if hasattr(r, "to_dict") else r for r in res]
        except Exception as e:
            print(f"Error in get_artifacts: {e}")
            traceback.print_exc()
            raise e

    async def download_artifact(self, url: str, dest_path: str):
        target_url = url if url.startswith("http") else f"{self.base_url}{url}"
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", target_url, headers=self.headers) as resp:
                resp.raise_for_status()
                with open(dest_path, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        f.write(chunk)
