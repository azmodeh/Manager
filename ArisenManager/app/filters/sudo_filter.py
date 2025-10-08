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
            sudo_config = config_loader.load_yaml("sudo_filter.yml")
            telegram_config = config_loader.get_telegram_config()
            
            config_keys = sudo_config["config_keys"]
            sudo_id = telegram_config.get(config_keys["primary"]) or telegram_config.get(config_keys["fallback"])
            
            if not sudo_id:
                logger.warning("Sudo ID not configured")
                return None
            
            if event.sender_id == sudo_id:
                return await func(event)
            else:
                logger.debug(text_loader.get_error("sudo_filter.access_denied", user_id=event.sender_id))
                return None
                
        except (KeyError, TypeError) as e:
            logger.error(text_loader.get_error("sudo_filter.permission_check_failed", error=f"Config error: {e}"))
            return None
        except RPCError as e:
            logger.error(text_loader.get_error("sudo_filter.permission_check_failed", error=f"Telegram error: {e}"))
            return None
        except Exception as e:
            logger.error(text_loader.get_error("sudo_filter.permission_check_failed", error=str(e)))
            return None
    
    return wrapper