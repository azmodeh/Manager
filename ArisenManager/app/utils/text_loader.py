from typing import Dict, Any, Optional
import yaml
import os
from pathlib import Path

class TextLoader:
    def __init__(self) -> None:
        self.base_path: Path = Path(__file__).parent.parent.parent / "data" / "texts"
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def load_catalog(self, filename: str) -> Dict[str, Any]:
        if filename not in self._cache:
            file_path = self.base_path / filename
            with open(file_path, 'r', encoding='utf-8') as f:
                self._cache[filename] = yaml.safe_load(f)
        return self._cache[filename]
    
    def get_text(self, key: str, lang: str = "fa", **kwargs: Any) -> str:
        catalog_file = f"messages_{lang}.yml"
        if lang == "en":
            catalog_file = "messages_en.yml"
        
        catalog = self.load_catalog(catalog_file)
        
        keys = key.split('.')
        text = catalog
        for k in keys:
            text = text.get(k, {})
        
        if isinstance(text, str):
            return text.format(**kwargs)
        return str(text)
    
    def get_error(self, key: str, **kwargs: Any) -> str:
        catalog = self.load_catalog("errors.yml")
        keys = key.split('.')
        text = catalog
        for k in keys:
            text = text.get(k, {})
        
        if isinstance(text, str):
            return text.format(**kwargs)
        return str(text)
    
    def get_emoji(self, key: str) -> str:
        catalog = self.load_catalog("emojis.yml")
        keys = key.split('.')
        emoji = catalog
        for k in keys:
            emoji = emoji.get(k, "")
        return str(emoji)

text_loader = TextLoader()