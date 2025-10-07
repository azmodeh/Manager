from typing import Dict, Any
import yaml
import os
from pathlib import Path

class ConfigLoader:
    def __init__(self) -> None:
        self.base_path: Path = Path(__file__).parent.parent.parent / "data" / "config"
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def load_config(self, filename: str) -> Dict[str, Any]:
        if filename not in self._cache:
            file_path = self.base_path / filename
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Replace environment variables
                for key, value in os.environ.items():
                    content = content.replace(f"${{{key}}}", value)
                self._cache[filename] = yaml.safe_load(content)
        return self._cache[filename]
    
    def get_telegram_config(self) -> Dict[str, Any]:
        return self.load_config("env.yml")["telegram"]
    
    def get_database_config(self) -> Dict[str, Any]:
        return self.load_config("env.yml")["database"]
    
    def get_database_url(self) -> str:
        db_config = self.get_database_config()
        return db_config.get("url", "")
    
    def get_keyboard_template(self, template_name: str) -> Dict[str, Any]:
        keyboards = self.load_config("keyboard.yml")
        return keyboards.get(template_name, {})

config_loader = ConfigLoader()