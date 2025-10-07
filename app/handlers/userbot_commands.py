from asyncio import sleep
from telethon.events import NewMessage
from app.services.userbot_connector import UserbotConnector
from app.core.logger import MessageLogger
from app.core.config_loader import ConfigLoader
from app.core.app_context import AppContext

logger = MessageLogger(__name__)
connector = UserbotConnector()
config_loader = ConfigLoader()
messages = config_loader.load_texts("fa")
join_prefix = config_loader.load_yaml("env.yml")["app"].get("join_command_prefix", "JOIN_GROUP:")


async def handle_join_command(event: NewMessage.Event) -> None:
    """Handle JOIN_GROUP command from bot."""
    if not event.is_private or not event.client:
        return
    
    try:
        data = event.message.text.replace(join_prefix, "").strip()
        parts = data.split("|")
        invite_link = parts[0].strip()
        chat_id = int(parts[1].strip()) if len(parts) > 1 else None
        
        success = await connector.join_group_by_link(event.client, invite_link)
        
        if success:
            await event.reply(messages.get("join_success", ""))
            if chat_id:
                await sleep(2)
                bot_client = AppContext().get_bot()
                if bot_client:
                    me = await event.client.get_me()
                    await connector.promote_to_admin(bot_client, chat_id, me.id)
        else:
            await event.reply(messages.get("join_failed", ""))
            
    except Exception as e:
        logger.error("join_command_error", error=str(e))
        await event.reply(messages.get("join_error", ""))


def register_handlers(userbot, bot) -> None:
    """Register userbot command handlers."""
    userbot.add_event_handler(
        handle_join_command,
        NewMessage(pattern=f"^{join_prefix}")
    )
    logger.info("handler_registered")