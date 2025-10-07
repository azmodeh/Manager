from telethon import events
from typing import Callable, Any

def private_filter(func: Callable) -> Callable:
    async def wrapper(event: events.NewMessage.Event) -> Any:
        if event.is_private:
            return await func(event)
        return None
    
    return wrapper