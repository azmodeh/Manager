from typing import Dict, Any, Optional
from pathlib import Path
import os
from app.core.config_cache import ConfigCache


class ConfigLoader:
    """Configuration loader for YAML files and environment variables."""
    
    def __init__(self) -> None:
        self.base_path = Path(__file__).parent.parent.parent / "data"
        self._cache = ConfigCache()
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file with cache."""
        return self._cache.get_config(filename)
    
    def load_texts(self, language: str) -> Dict[str, Any]:
        """Load text messages with cache."""
        return self._cache.get_texts(language)
    
    def get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable value."""
        return os.getenv(key, default)