import logging
from telethon import events
from typing import Callable, Any

logger = logging.getLogger(__name__)

def group_filter(func: Callable) -> Callable:
    async def wrapper(event: events.NewMessage.Event) -> Any:
        try:
            if event.is_group or event.is_channel:
                return await func(event)
            else:
                logger.debug(f"Message from private chat {event.chat_id}, group filter applied")
                return None
        except Exception as e:
            logger.error(f"Group filter error: {e}")
            return None
    
    return wrapper