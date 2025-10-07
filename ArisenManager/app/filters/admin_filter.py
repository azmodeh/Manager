from telethon import events
from typing import Callable, Any

def admin_filter(func: Callable) -> Callable:
    async def wrapper(event: events.NewMessage.Event) -> Any:
        if event.is_group or event.is_channel:
            try:
                permissions = await event.client.get_permissions(event.chat_id, event.sender_id)
                if permissions.is_admin or permissions.is_creator:
                    return await func(event)
            except:
                pass
        return None
    
    return wrapper