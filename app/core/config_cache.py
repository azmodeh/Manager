from typing import Dict, Any
from pathlib import Path
import yaml


class ConfigCache:
    """Configuration cache with auto-reload."""
    
    _cache: Dict[str, Dict[str, Any]] = {}
    _timestamps: Dict[str, float] = {}
    _base_path = Path(__file__).parent.parent.parent / "data"
    
    @classmethod
    def _load(cls, key: str, filepath: Path) -> Dict[str, Any]:
        """Load and cache file if modified."""
        mtime = filepath.stat().st_mtime
        if key not in cls._timestamps or mtime > cls._timestamps[key]:
            with open(filepath, "r", encoding="utf-8") as f:
                cls._cache[key] = yaml.safe_load(f)
            cls._timestamps[key] = mtime
        return cls._cache[key]
    
    @classmethod
    def get_config(cls, filename: str) -> Dict[str, Any]:
        """Get configuration with auto-reload."""
        return cls._load(f"config_{filename}", cls._base_path / "config" / filename)
    
    @classmethod
    def get_texts(cls, language: str) -> Dict[str, Any]:
        """Get text messages with auto-reload."""
        filename = f"messages_{language}.yml"
        return cls._load(f"texts_{filename}", cls._base_path / "texts" / filename)
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cache."""
        cls._cache.clear()
        cls._timestamps.clear()
