
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from rice_factor.config.settings import settings
from rice_factor_web.backend.api.v1.configuration import ConfigResponse, _project_config_file, _user_config_file

def test_get_config():
    print("Testing settings.as_dict()...")
    try:
        merged = settings.as_dict()
        print(f"Merged settings type: {type(merged)}")
        print(f"Merged settings keys: {merged.keys()}")
    except Exception as e:
        print(f"Error getting settings dict: {e}")
        return

    print("\nReading files...")
    project_content = None
    if _project_config_file.exists():
        try:
            print(f"Reading {_project_config_file}")
            project_content = _project_config_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading project config: {e}")

    user_content = None
    if _user_config_file.exists():
        try:
            print(f"Reading {_user_config_file}")
            user_content = _user_config_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading user config: {e}")
            
    print("\nValidating ConfigResponse...")
    try:
        response = ConfigResponse(
            merged=merged,
            project_config=project_content,
            user_config=user_content,
            project_config_path=str(_project_config_file.absolute()),
            user_config_path=str(_user_config_file.absolute()),
        )
        print("Success! Response model created.")
        
        from fastapi.encoders import jsonable_encoder
        print("Testing jsonable_encoder...")
        encoded = jsonable_encoder(response)
        print("Success! JSON encoder passed.")
        import json
        print(json.dumps(encoded, indent=2))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Validation/Encoding failed: {e}")

if __name__ == "__main__":
    test_get_config()
