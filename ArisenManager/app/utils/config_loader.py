import logging
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .text_loader import text_loader

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class ConfigLoader:
    def __init__(self) -> None:
        self.base_path: Path = Path(__file__).parent.parent.parent
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._config: Optional[Dict[str, Any]] = None
        self._load_loader_config()
    
    def _load_loader_config(self) -> None:
        """Load config loader's own configuration"""
        try:
            config_path = self.base_path / "data" / "config" / "config_loader.yml"
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            logger.error(text_loader.get_error("config_loader.init_error", error=str(e)))
            # Fallback configuration
            self._config = {
                "paths": {"config_dir": "data/config"},
                "allowed_files": ["env.yml", "keyboard.yml"],
                "config_keys": {"telegram": "telegram", "database": "database"},
                "file_encoding": "utf-8",
                "file_mode": "r"
            }
    
    def _validate_filename(self, filename: str) -> bool:
        """Validate filename to prevent path traversal"""
        if not self._config:
            return False
            
        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            logger.warning(text_loader.get_error("config_loader.path_traversal_attempt", filename=filename))
            return False
        
        # Check if filename is in allowed list
        allowed_files = self._config.get("allowed_files", [])
        if filename not in allowed_files:
            logger.warning(text_loader.get_error("config_loader.invalid_filename", filename=filename))
            return False
        
        return True
    
    def load_config(self, filename: str) -> Dict[str, Any]:
        """Load configuration file with security validation"""
        if not self._validate_filename(filename):
            return {}
        
        if filename not in self._cache:
            try:
                config_dir = self._config["paths"]["config_dir"]
                file_path = self.base_path / config_dir / filename
                
                if not file_path.exists():
                    logger.error(text_loader.get_error("config_loader.file_not_found", filename=filename))
                    return {}
                
                encoding = self._config["file_encoding"]
                mode = self._config["file_mode"]
                
                with open(file_path, mode, encoding=encoding) as f:
                    content = f.read()
                    
                    # Replace environment variables with whitelist validation
                    allowed_env_vars = self._config.get("allowed_env_vars", ["TELEGRAM_BOT_TOKEN", "DATABASE_URL"])
                    for key in allowed_env_vars:
                        if key in os.environ:
                            value = os.environ[key]
                            # Strict path traversal validation
                            import re
                            # Block any path traversal patterns
                            dangerous_patterns = ["..", "%2e", "%2f", "%5c", "file://"]
                            has_traversal = any(pattern in value.lower() for pattern in dangerous_patterns)
                            # Only allow alphanumeric, common URL chars, and known safe protocols
                            is_safe_format = re.match(r'^[a-zA-Z0-9:/.@_-]+$', value)
                            is_safe = is_safe_format and not has_traversal and len(value) < 500
                            
                            if is_safe:
                                content = content.replace(f"${{{key}}}", value)
                            else:
                                logger.warning(text_loader.get_error("config_loader.env_path_traversal", key=key))
                    
                    self._cache[filename] = yaml.safe_load(content) or {}
                    
            except FileNotFoundError:
                logger.error(text_loader.get_error("config_loader.file_not_found", filename=filename))
                return {}
            except yaml.YAMLError as e:
                logger.error(text_loader.get_error("config_loader.yaml_parse_error", filename=filename, error=str(e)))
                return {}
            except Exception as e:
                logger.error(text_loader.get_error("config_loader.file_read_error", filename=filename, error=str(e)))
                return {}
        
        return self._cache[filename]
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Alias for load_config for backward compatibility"""
        return self.load_config(filename)
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """Get Telegram configuration"""
        config_key = self._config["config_keys"]["telegram"]
        env_config = self.load_config("env.yml")
        return env_config.get(config_key, {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        config_key = self._config["config_keys"]["database"]
        env_config = self.load_config("env.yml")
        return env_config.get(config_key, {})
    
    def get_database_url(self) -> str:
        """Get database URL"""
        db_config = self.get_database_config()
        url_key = self._config["config_keys"]["url"]
        return db_config.get(url_key, "")
    
    def get_keyboard_template(self, template_name: str) -> Dict[str, Any]:
        """Get keyboard template"""
        keyboards = self.load_config("keyboard.yml")
        return keyboards.get(template_name, {})
    
    def clear_cache(self) -> None:
        """Clear configuration cache"""
        self._cache.clear()

config_loader = ConfigLoader()