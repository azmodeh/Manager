import logging
from typing import Optional
from ..utils.config_loader import config_loader

class Logger:
    def __init__(self) -> None:
        self._logger: Optional[logging.Logger] = None
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        self._logger = logging.getLogger("ArisenManager")
        
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)
    
    def info(self, message: str) -> None:
        if self._logger:
            self._logger.info(message)
    
    def warning(self, message: str) -> None:
        if self._logger:
            self._logger.warning(message)
    
    def error(self, message: str) -> None:
        if self._logger:
            self._logger.error(message)
    
    def debug(self, message: str) -> None:
        if self._logger:
            self._logger.debug(message)

logger = Logger()