import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TextLoader:
    def __init__(self) -> None:
        self.base_path: Path = Path(__file__).parent.parent.parent
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._config: Optional[Dict[str, Any]] = None
        self._load_loader_config()
    
    def _load_loader_config(self) -> None:
        """Load text loader's own configuration"""
        try:
            config_path = self.base_path / "data" / "config" / "text_loader.yml"
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load text loader configuration: {e}")
            # Fallback configuration
            self._config = {
                "paths": {"texts_dir": "data/texts"},
                "allowed_files": ["messages_fa.yml", "messages_en.yml", "errors.yml", "emojis.yml"],
                "file_templates": {"messages": "messages_{lang}.yml", "errors": "errors.yml", "emojis": "emojis.yml"},
                "languages": {"default": "fa", "supported": ["fa", "en"]},
                "file_settings": {"encoding": "utf-8", "mode": "r"},
                "fallback": {"text": "", "error": "Error: {key}", "emoji": ""}
            }
    
    def _validate_filename(self, filename: str) -> bool:
        """Validate filename to prevent path traversal"""
        if not self._config:
            return False
            
        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            logger.warning(f"Path traversal attempt detected: {filename}")
            return False
        
        # Check if filename is in allowed list
        allowed_files = self._config.get("allowed_files", [])
        if filename not in allowed_files:
            logger.warning(f"Invalid text catalog filename: {filename}")
            return False
        
        return True
    
    def load_catalog(self, filename: str) -> Dict[str, Any]:
        """Load text catalog with security validation"""
        if not self._validate_filename(filename):
            return {}
        
        if filename not in self._cache:
            try:
                texts_dir = self._config["paths"]["texts_dir"]
                file_path = self.base_path / texts_dir / filename
                
                if not file_path.exists():
                    logger.error(f"Text catalog file not found: {filename}")
                    return {}
                
                file_settings = self._config["file_settings"]
                with open(file_path, file_settings["mode"], encoding=file_settings["encoding"]) as f:
                    self._cache[filename] = yaml.safe_load(f) or {}
                    
            except FileNotFoundError:
                logger.error(f"Text catalog file not found: {filename}")
                return {}
            except yaml.YAMLError as e:
                logger.error(f"YAML parse error in {filename}: {e}")
                return {}
            except Exception as e:
                logger.error(f"Error reading text catalog {filename}: {e}")
                return {}
        
        return self._cache[filename]
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, {})
            else:
                return None
        return value
    
    def get_text(self, key: str, lang: str = None, **kwargs: Any) -> str:
        """Get text from catalog with language support"""
        try:
            if lang is None:
                lang = self._config["languages"]["default"]
            
            # Validate language
            supported_langs = self._config["languages"]["supported"]
            if lang not in supported_langs:
                lang = self._config["languages"]["default"]
            
            # Build filename
            template = self._config["file_templates"]["messages"]
            catalog_file = template.format(lang=lang)
            
            catalog = self.load_catalog(catalog_file)
            if not catalog:
                return self._config["fallback"]["text"]
            
            text = self._get_nested_value(catalog, key)
            
            if isinstance(text, str):
                try:
                    return text.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Text formatting error for key {key}: {e}")
                    return text
            
            return self._config["fallback"]["text"]
            
        except Exception as e:
            logger.error(f"Error getting text for key {key}: {e}")
            return self._config["fallback"]["text"]
    
    def get_error(self, key: str, **kwargs: Any) -> str:
        """Get error message from catalog"""
        try:
            catalog_file = self._config["file_templates"]["errors"]
            catalog = self.load_catalog(catalog_file)
            
            if not catalog:
                return self._config["fallback"]["error"].format(key=key)
            
            text = self._get_nested_value(catalog, key)
            
            if isinstance(text, str):
                try:
                    return text.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error formatting error message for key {key}: {e}")
                    return text
            
            return self._config["fallback"]["error"].format(key=key)
            
        except Exception as e:
            logger.error(f"Error getting error message for key {key}: {e}")
            return self._config["fallback"]["error"].format(key=key)
    
    def get_emoji(self, key: str) -> str:
        """Get emoji from catalog"""
        try:
            catalog_file = self._config["file_templates"]["emojis"]
            catalog = self.load_catalog(catalog_file)
            
            if not catalog:
                return self._config["fallback"]["emoji"]
            
            emoji = self._get_nested_value(catalog, key)
            
            if isinstance(emoji, str):
                return emoji
            
            return self._config["fallback"]["emoji"]
            
        except Exception as e:
            logger.error(f"Error getting emoji for key {key}: {e}")
            return self._config["fallback"]["emoji"]
    
    def clear_cache(self) -> None:
        """Clear text catalog cache"""
        self._cache.clear()

text_loader = TextLoader()