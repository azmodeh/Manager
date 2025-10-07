import logging
import logging.config
from typing import Any
from app.core.config_loader import ConfigLoader


def setup_logging() -> None:
    """Setup logging configuration from YAML file."""
    logging.config.dictConfig(ConfigLoader().load_yaml("logging.yml"))


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)


class MessageLogger:
    """Logger wrapper for internationalized messages."""
    
    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name)
        self.messages = ConfigLoader().load_texts("en")
    
    def _log(self, level: str, message_key: str, **kwargs: Any) -> None:
        """Log message using message key."""
        message = self.messages.get(message_key, message_key)
        getattr(self.logger, level)(message, extra=kwargs)
    
    def info(self, message_key: str, **kwargs: Any) -> None:
        self._log("info", message_key, **kwargs)
    
    def error(self, message_key: str, **kwargs: Any) -> None:
        self._log("error", message_key, **kwargs)
    
    def warning(self, message_key: str, **kwargs: Any) -> None:
        self._log("warning", message_key, **kwargs)