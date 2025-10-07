from telethon.events import NewMessage, ChatAction
from telethon.tl.types import KeyboardButtonCallback
from app.utils.auth import AuthFilter
from app.utils.replies import ReplyHelper
from app.repos.group_repo import GroupRepository
from app.core.logger import MessageLogger
from app.core.config_loader import ConfigLoader

logger = MessageLogger(__name__)
auth = AuthFilter()
reply_helper = ReplyHelper()
group_repo = GroupRepository()
config_loader = ConfigLoader()
    
async def handle_bot_added(event: ChatAction.Event) -> None:
    """Handle bot being added to group."""
    if not event.user_added or not event.client:
        return
    
    bot_id = (await event.client.get_me()).id
    if event.user_id != bot_id:
        return
    
    try:
        chat = await event.get_chat()
        if not chat or not event.chat_id:
            return
        
        chat_title = getattr(chat, 'title', 'Unknown')
        await group_repo.add_pending_group(event.chat_id, chat_title)
        
        config = config_loader.load_yaml("env.yml")
        messages = config_loader.load_texts("fa")
        
        sudo_id = config["telegram"]["sudo"]
        approve_prefix = config["app"].get("approve_prefix", "APPROVE")
        reject_prefix = config["app"].get("reject_prefix", "REJECT")
        
        buttons = [[
            KeyboardButtonCallback(
                messages.get("approve_button", ""),
                f"{approve_prefix}|{event.chat_id}".encode()
            ),
            KeyboardButtonCallback(
                messages.get("reject_button", ""),
                f"{reject_prefix}|{event.chat_id}".encode()
            )
        ]]
        
        await reply_helper.send_text_to_user(
            event.client,
            sudo_id,
            messages.get("approval_request", "").format(
                title=chat_title,
                chat_id=event.chat_id
            ),
            buttons=buttons
        )
        
        await event.client.send_message(
            event.chat_id,
            messages.get("group_pending", "")
        )
        
    except Exception as e:
        logger.error("group_approval_error", error=str(e))
    
async def handle_approval_callback(event) -> None:
    """Handle group approval callback."""
    if not await auth.is_sudo(event.sender_id):
        messages = config_loader.load_texts("fa")
        await event.answer(messages.get("missing_permission", ""))
        return
    
    try:
        config = config_loader.load_yaml("env.yml")
        messages = config_loader.load_texts("fa")
        
        data = event.data.decode()
        parts = data.split(config["app"].get("callback_separator", "|"))
        
        if len(parts) != 2:
            return
        
        action, chat_id = parts[0], int(parts[1])
        approve_prefix = config["app"].get("approve_prefix", "APPROVE")
        reject_prefix = config["app"].get("reject_prefix", "REJECT")
        
        if action == approve_prefix:
            success = await group_repo.approve_group(chat_id)
            if success:
                await event.answer(messages.get("group_approved_msg", ""))
                await reply_helper.send_text_to_user(
                    event.client,
                    chat_id,
                    messages.get("group_approved", "")
                )
            else:
                await event.answer(messages.get("approval_error", ""))
        
        elif action == reject_prefix:
            await event.answer(messages.get("group_rejected", ""))
            await event.client.kick_participant(chat_id, "me")
            
    except Exception as e:
        logger.error("approval_callback_error", error=str(e))
    
async def add_userbot_to_group(bot_client, userbot, chat_id: int) -> None:
    """Add userbot to approved group."""
    try:
        from app.services.userbot_connector import UserbotConnector
        await UserbotConnector().send_join_request(bot_client, userbot, chat_id)
    except Exception as e:
        logger.error("userbot_join_error", error=str(e))


def register_handlers(userbot, bot) -> None:
    """Register group approval handlers."""
    bot.add_event_handler(handle_bot_added, ChatAction)
    logger.info("handler_registered")