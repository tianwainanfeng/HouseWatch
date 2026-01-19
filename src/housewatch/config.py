# src/housewatch/config.py

from pathlib import Path
from housewatch.utils.load_config import load_config


class ProjectConfig:
    """Load all configurations with optional .local.yaml replacement"""
    
    def __init__(self):

        self.email = self._load("configs/email.yaml", "email")
        self.criteria = self._load("configs/criteria.yaml", "criteria")
        self.app = self._load("configs/app.yaml", "app")


    def _load(self, base_path: str, root_key: str):
        """
        Load <name>.local.yaml if it exists, otherwise <name>.yaml
        """

        path = Path(base_path)

        local_path = path.with_name(
            path.stem + ".local" + path.suffix
        )

        target = str(local_path) if local_path.exists() else base_path
        data = load_config(target)

        return data.get(root_key, data)
    
    
    def get(self, key, default=None):
        return getattr(self, key, default)