from telethon.events import NewMessage, ChatAction
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from app.utils.auth import AuthFilter
from app.utils.replies import ReplyHelper
from app.repos.group_repo import GroupRepository
from app.services.buttons import ButtonService
from app.core.logger import MessageLogger

logger = MessageLogger(__name__)
auth = AuthFilter()
reply_helper = ReplyHelper()
group_repo = GroupRepository()
button_service = ButtonService()


class RulesWelcomeHandler:
    """Handler for group rules and welcome messages."""
    
    async def _send_feature_message(self, event, feature_name: str) -> None:
        """Common logic for sending feature messages."""
        if not event.chat_id:
            return
        
        config = await group_repo.get_group_feature(event.chat_id, feature_name)
        if not config or config.enabled is not True:
            return
        
        buttons = None
        if config.buttons_json is not None:
            buttons = button_service.parse_buttons(str(config.buttons_json))
        
        text = str(config.text) if config.text is not None else ""
        
        if config.media_pointer is not None:
            await event.reply(text, buttons=buttons)
        else:
            await reply_helper.reply_text(event, text, buttons=buttons)
    
    async def handle_rules(self, event: NewMessage.Event) -> None:
        """Handle /rules command."""
        if not await auth.is_group(event):
            return
        
        try:
            await self._send_feature_message(event, "rules")
        except Exception as e:
            logger.error("error_database", error=str(e))
    
    async def handle_welcome(self, event: ChatAction.Event) -> None:
        """Handle user join for welcome message."""
        if not event.user_joined and not event.user_added:
            return
        
        try:
            await self._send_feature_message(event, "welcome")
        except Exception as e:
            logger.error("error_database", error=str(e))


def register_handlers(userbot, bot) -> None:
    """Register rules and welcome handlers.
    
    Args:
        userbot: Userbot client
        bot: Bot API client
    """
    handler = RulesWelcomeHandler()
    
    bot.add_event_handler(
        handler.handle_rules,
        NewMessage(pattern=r"^/rules$")
    )
    
    bot.add_event_handler(
        handler.handle_welcome,
        ChatAction
    )
    
    logger.info("handler_registered")