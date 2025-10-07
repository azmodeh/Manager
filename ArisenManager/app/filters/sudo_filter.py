from telethon import events
from typing import Callable, Any
from ..utils.config_loader import config_loader

def sudo_filter(func: Callable) -> Callable:
    async def wrapper(event: events.NewMessage.Event) -> Any:
        config = config_loader.get_telegram_config()
        sudo_id = config.get("sudo_id") or config.get("sudo")
        
        if event.sender_id == sudo_id:
            return await func(event)
        return None
    
    return wrapper