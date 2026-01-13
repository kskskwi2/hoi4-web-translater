import os
import sys
import ctypes.wintypes
import pathlib
import time

def get_docs_path():
    try:
        CSIDL_PERSONAL = 5
        SHGFP_TYPE_CURRENT = 0
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
        return buf.value
    except Exception as e:
        print(f"Error getting documents path: {e}")
        return None

def debug_path_access(target_path):
    print(f"\n--- Debugging Path: {target_path} ---")
    
    # Check hierarchy
    parts = pathlib.Path(target_path).parts
    current = pathlib.Path(parts[0])
    print(f"Checking hierarchy for: {target_path}")
    
    for part in parts[1:]:
        current = current / part
        exists = current.exists()
        is_dir = current.is_dir() if exists else False
        print(f"  {current} -> Exists: {exists}, IsDir: {is_dir}")
        if not exists:
            print(f"    ! Stops existing here.")
            # Try to create
            try:
                os.makedirs(current, exist_ok=True)
                print(f"    + Created: {current}")
            except Exception as e:
                print(f"    x Failed to create: {e}")
                return False

    # Final check
    if not os.path.exists(target_path):
        print(f"❌ Target path still does not exist: {target_path}")
        return False
        
    # Write Test
    test_file = os.path.join(target_path, ".debug_write_test")
    print(f"Attempting to write: {test_file}")
    try:
        with open(test_file, "w") as f:
            f.write("test")
        print("✅ Write Success!")
        os.remove(test_file)
        print("✅ Delete Success!")
        return True
    except Exception as e:
        print(f"❌ Write Failed: {e}")
        return False

if __name__ == "__main__":
    print(f"Current Working Dir: {os.getcwd()}")
    
    docs_root = get_docs_path()
    print(f"Detected Documents Root via API: {docs_root}")
    
    if docs_root:
        paradox_path = os.path.join(docs_root, "Paradox Interactive", "Hearts of Iron IV", "mod")
        success = debug_path_access(paradox_path)
        
        if success:
            print("\n🎉 SUCCESS: The path is accessible and writable.")
        else:
            print("\n💀 FAILURE: Could not write to the path.")
    
    print("\n--- Testing Local Fallback Logic ---")
    local_fallback = os.path.join(os.getcwd(), "generated_mods")
    debug_path_access(local_fallback)
