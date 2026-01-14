import httpx
import os
import zipfile
import io

class ParatranzService:
    BASE_URL = "https://paratranz.cn/api"

    def __init__(self, token: str):
        self.token = token
        self.headers = {"Authorization": token}

    async def get_projects(self):
        async with httpx.AsyncClient() asclient:
            resp = await client.get(f"{self.BASE_URL}/projects", headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def get_files(self, project_id: int):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/projects/{project_id}/files", 
                headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()

    async def trigger_export(self, project_id: int):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/projects/{project_id}/artifacts",
                headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()

    async def download_artifact(self, project_id: int, dest_path: str):
        """
        Downloads the latest artifact (zip) and extracts it to dest_path.
        Returns the list of extracted files.
        """
        async with httpx.AsyncClient() as client:
            # 1. Get artifact info
            resp = await client.get(
                f"{self.BASE_URL}/projects/{project_id}/artifacts",
                headers=self.headers
            )
            resp.raise_for_status()
            artifacts = resp.json()
            
            if not artifacts:
                raise Exception("No artifacts found. Please trigger an export first.")

            # Assume the first one is the latest
            latest_artifact = artifacts[0]
            download_url = f"{self.BASE_URL}/artifacts/{latest_artifact['id']}" # Note: Download URL format might vary

            # Wait, the artifact object usually has a download URL or we build it
            # The API docs say GET /projects/:projectId/artifacts returns list
            # We then download via url provided in response or constructing it.
            # Let's try direct download if url field exists, otherwise use standard pattern
            
            # Correction: Paratranz often provides a direct download link in the response `url` field
            # If not, we try standard endpoint
            dl_url = latest_artifact.get('url') or f"{self.BASE_URL}/projects/{project_id}/artifacts/download"

            # 2. Download ZIP
            print(f"Downloading artifact from {dl_url}...")
            resp = await client.get(dl_url, headers=self.headers, follow_redirects=True)
            resp.raise_for_status()

            # 3. Extract
            os.makedirs(dest_path, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                z.extractall(dest_path)
                return z.namelist()
