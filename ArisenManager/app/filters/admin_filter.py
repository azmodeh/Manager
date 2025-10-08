import logging
from telethon import events
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError, ChannelPrivateError
from typing import Callable, Any
from ..utils.text_loader import text_loader

logger = logging.getLogger(__name__)

def admin_filter(func: Callable) -> Callable:
    async def wrapper(event: events.NewMessage.Event) -> Any:
        if event.is_group or event.is_channel:
            try:
                permissions = await event.client.get_permissions(event.chat_id, event.sender_id)
                if permissions.is_admin or permissions.is_creator:
                    return await func(event)
                else:
                    logger.debug(text_loader.get_error("admin_filter.not_admin", 
                                                     user_id=event.sender_id, 
                                                     chat_id=event.chat_id))
                    return None
            except (ChatAdminRequiredError, UserNotParticipantError, ChannelPrivateError) as e:
                logger.warning(text_loader.get_error("admin_filter.permission_check_failed", error=str(e)))
                return None
            except Exception as e:
                logger.error(text_loader.get_error("admin_filter.permission_check_failed", error=str(e)))
                return None
        return None
    
    return wrapper