import logging
from telethon import events
from telethon.errors import RPCError
from typing import Callable, Any
from ..utils.config_loader import config_loader
from ..utils.text_loader import text_loader

logger = logging.getLogger(__name__)

def sudo_filter(func: Callable) -> Callable:
    async def wrapper(event: events.NewMessage.Event) -> Any:
        try:
            telegram_config = config_loader.get_telegram_config()
            sudo_id = telegram_config.get("sudo") or telegram_config.get("sudo_id")
            
            if sudo_id and event.sender_id == sudo_id:
                return await func(event)
            return None
                
        except Exception:
            return None
    
    return wrapper