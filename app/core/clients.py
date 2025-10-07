from typing import Tuple
from telethon import TelegramClient
from telethon.sessions import StringSession
from pathlib import Path
from app.core.config_loader import ConfigLoader
from app.core.logger import MessageLogger

logger = MessageLogger(__name__)


class ClientManager:
    """Telegram clients manager."""
    
    def __init__(self) -> None:
        self.config = ConfigLoader().load_yaml("env.yml")
        self.telegram = self.config["telegram"]
        self.sessions_path = Path(__file__).parent.parent.parent / "data" / "sessions"
        self.sessions_path.mkdir(exist_ok=True)
    
    def get_clients(self) -> Tuple[TelegramClient, TelegramClient]:
        """Get both userbot and bot clients."""
        api_id = self.telegram["api_id"]
        api_hash = self.telegram["api_hash"]
        
        session_string = self.telegram.get("session_string")
        userbot = TelegramClient(
            StringSession(session_string) if session_string else str(self.sessions_path / self.telegram["session_userbot"]),
            api_id,
            api_hash
        )
        logger.info("startup_userbot")
        
        bot = TelegramClient(
            str(self.sessions_path / self.telegram["session_bot"]),
            api_id,
            api_hash
        )
        logger.info("startup_botapi")
        
        return userbot, bot