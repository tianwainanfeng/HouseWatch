# src/housewatch/utils/load_config.py

import os
import re
import yaml
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# Auto search and load env variables defined in .env
# override=False # Ensure same environment variable not be overrided by .env
root_dir = Path(__file__).resolve().parent.parent.parent.parent
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)


def load_config(path: str) -> Dict:
    """
    YAML loader
    - Auto path (Path.resolve)
    - Auto load env variables (${VAR_NAME})
    """
    path_obj = Path(path).expanduser().resolve()

    if not path_obj.exists():
        raise FileNotFoundError(f"Cannot find: {path_obj}")

    with open(path_obj, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Search ${VAR_NAME}
    pattern = re.compile(r'\$\{(\w+)\}')

    def replacer(match):
        env_var = match.group(1)
        value = os.getenv(env_var)

        if value is None:
            print(f"Warning: environment variable '${env_var}' not found!")
            return match.group(0)
        
        return value
    
    substituted_content = pattern.sub(replacer, content)

    return yaml.safe_load(substituted_content)
    
