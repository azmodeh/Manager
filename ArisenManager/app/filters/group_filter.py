from telethon import events
from typing import Callable, Any

def group_filter(func: Callable) -> Callable:
    async def wrapper(event: events.NewMessage.Event) -> Any:
        if event.is_group or event.is_channel:
            return await func(event)
        return None
    
    return wrapper