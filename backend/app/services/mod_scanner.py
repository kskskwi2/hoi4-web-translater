import os
import glob
from .parser import ParadoxParser


class ModScanner:
    def __init__(self):
        pass

    def scan_workshop(self, workshop_path: str):
        """
        Scans all folders in the workshop path for descriptor.mod.
        Returns a list of mod objects.
        """
        mods = []

        # Ensure path exists and is absolute
        if not workshop_path:
            return {"error": "Workshop path is empty", "mods": []}

        workshop_path = os.path.abspath(workshop_path)

        if not os.path.exists(workshop_path):
            print(f"DEBUG: Workshop path does not exist: {workshop_path}")
            return {"error": "Path does not exist", "mods": []}

        print(f"DEBUG: Scanning workshop path: {workshop_path}")

        # Iterate over directories
        for entry in os.scandir(workshop_path):
            if entry.is_dir():
                mod_id = entry.name
                descriptor_path = os.path.join(entry.path, "descriptor.mod")

                # Case-insensitive check for descriptor.mod
                if not os.path.exists(descriptor_path):
                    # Try uppercase or other variations if needed, but standard is lowercase
                    pass

                if os.path.exists(descriptor_path):
                    try:
                        mod_info = ParadoxParser.parse_file(descriptor_path)

                        # Add metadata
                        mod_info["id"] = mod_id
                        mod_info["path"] = entry.path.replace("\\", "/")

                        # Handle thumbnail
                        if "picture" in mod_info:
                            thumb_path = os.path.join(entry.path, mod_info["picture"])
                            mod_info["thumbnail_path"] = (
                                thumb_path if os.path.isfile(thumb_path) else None
                            )

                        mods.append(mod_info)
                    except Exception as e:
                        print(f"Error parsing mod {mod_id}: {e}")

        print(f"DEBUG: Found {len(mods)} mods")
        return {"mods": mods}
