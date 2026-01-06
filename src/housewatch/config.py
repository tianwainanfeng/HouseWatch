# src/housewatch/config.py

from housewatch.utils.load_config import load_config


class ProjectConfig:
    """Load all configurations"""
    def __init__(self):
        # Load email.yaml
        email_data = load_config("configs/email.yaml")
        self.email = email_data.get('email', email_data)

        # Load criteria.yaml
        criteria_raw = load_config("configs/criteria.yaml")
        self.criteria = criteria_raw.get('criteria', criteria_raw)

        # Load app.yaml
        app_config = load_config("configs/app.yaml")
        self.app = app_config.get("search", app_config)
    
    def get(self, key, default=None):
        return getattr(self, key, default)