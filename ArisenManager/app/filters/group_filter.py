import logging
from telethon import events
from typing import Callable, Any
from ..utils.text_loader import text_loader

logger = logging.getLogger(__name__)

def group_filter(func: Callable) -> Callable:
    async def wrapper(event: events.NewMessage.Event) -> Any:
        try:
            if event.is_group or event.is_channel:
                return await func(event)
            else:
                logger.debug(text_loader.get_error("group_filter.private_chat_blocked", chat_id=event.chat_id))
                return None
        except Exception as e:
            logger.error(text_loader.get_error("group_filter.error", error=str(e)))
            return None
    
    return wrapper