from telethon.events import CallbackQuery
from app.utils.auth import AuthFilter
from app.repos.group_repo import GroupRepository
from app.services.userbot_connector import UserbotConnector
from app.core.app_context import AppContext
from app.core.logger import MessageLogger
from app.core.config_loader import ConfigLoader

logger = MessageLogger(__name__)
auth = AuthFilter()
group_repo = GroupRepository()
connector = UserbotConnector()
config_loader = ConfigLoader()

# Cache config data
messages = config_loader.load_texts("fa")
config = config_loader.load_yaml("env.yml")
app_config = config["app"]
separator = app_config.get("callback_separator", "|")
approve_prefix = app_config.get("approve_prefix", "APPROVE")
reject_prefix = app_config.get("reject_prefix", "REJECT")


async def handle_approval_callback(event: CallbackQuery.Event) -> None:
    """Handle group approval callback."""
    if not event.sender_id or not await auth.is_sudo(event.sender_id):
        await event.answer(messages.get("missing_permission", ""))
        return
    
    try:
        parts = event.data.decode().split(separator)
        if len(parts) != 2:
            return
        
        action, chat_id = parts[0], int(parts[1])
        
        if action == approve_prefix:
            success = await group_repo.approve_group(chat_id)
            if success:
                await event.answer(messages.get("group_approved_msg", ""))
                if event.client:
                    await event.client.send_message(chat_id, messages.get("group_approved", ""))
                    
                    userbot = AppContext().get_userbot()
                    if userbot:
                        await connector.send_join_request(event.client, userbot, chat_id)
            else:
                await event.answer(messages.get("approval_error", ""))
        
        elif action == reject_prefix:
            await event.answer(messages.get("group_rejected", ""))
            if event.client:
                await event.client.kick_participant(chat_id, "me")
    
    except Exception as e:
        logger.error("approval_callback_error", error=str(e))


def register_handlers(userbot, bot) -> None:
    """Register approval callback handlers."""
    bot.add_event_handler(
        handle_approval_callback,
        CallbackQuery(pattern=f"^({approve_prefix}|{reject_prefix})")
    )
    logger.info("handler_registered")