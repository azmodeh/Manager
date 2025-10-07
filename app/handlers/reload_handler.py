from telethon.events import NewMessage
from app.utils.auth import AuthFilter
from app.utils.replies import ReplyHelper
from app.core.logger import MessageLogger

logger = MessageLogger(__name__)
auth = AuthFilter()
reply_helper = ReplyHelper()


async def handle_reload(event: NewMessage.Event) -> None:
    """Handle /reload command."""
    if not await auth.is_sudo(event.sender_id):
        await reply_helper.reply(event, "missing_permission")
        return
    
    try:
        from app.core.config_cache import ConfigCache
        ConfigCache().clear_cache()
        
        await reply_helper.reply(event, "reload_success")
        logger.info("config_reloaded")
        
    except Exception as e:
        logger.error("reload_failed", error=str(e))
        await reply_helper.reply(event, "reload_failed")


def register_handlers(userbot, bot) -> None:
    """Register reload handlers."""
    bot.add_event_handler(
        handle_reload,
        NewMessage(pattern=r"^/reload$")
    )
    
    logger.info("handler_registered")
