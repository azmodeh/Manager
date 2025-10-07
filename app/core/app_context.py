from typing import Optional
from telethon import TelegramClient


class AppContext:
    """Global application context for sharing clients."""
    
    _userbot: Optional[TelegramClient] = None
    _bot: Optional[TelegramClient] = None
    
    @classmethod
    def set_clients(cls, userbot: TelegramClient, bot: TelegramClient) -> None:
        """Set client instances."""
        cls._userbot = userbot
        cls._bot = bot
    
    @classmethod
    def get_userbot(cls) -> Optional[TelegramClient]:
        """Get userbot client."""
        return cls._userbot
    
    @classmethod
    def get_bot(cls) -> Optional[TelegramClient]:
        """Get bot client."""
        return cls._bot