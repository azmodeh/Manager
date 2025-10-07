from telethon.events import NewMessage
from app.utils.auth import AuthFilter
from app.utils.replies import ReplyHelper
from app.repos.commands_repo import CommandsRepository
from app.core.logger import MessageLogger

logger = MessageLogger(__name__)
auth = AuthFilter()
reply_helper = ReplyHelper()
commands_repo = CommandsRepository()


async def _handle_command(event: NewMessage.Event, enabled_field: str, text_field: str, default_key: str) -> None:
    """Common logic for handling commands."""
    try:
        config = await commands_repo.get_global_commands()
        
        if not config or not getattr(config, enabled_field):
            await reply_helper.reply(event, default_key)
            return
        
        await reply_helper.reply_text(event, str(getattr(config, text_field)))
        
    except Exception as e:
        logger.error("error_database", error=str(e))
        await reply_helper.reply(event, default_key)

async def handle_start(event: NewMessage.Event) -> None:
    """Handle /start command."""
    await _handle_command(event, "start_enabled", "start_text", "start_default")

async def handle_help(event: NewMessage.Event) -> None:
    """Handle /help command."""
    await _handle_command(event, "help_enabled", "help_text", "help_default")


def register_handlers(userbot, bot) -> None:
    """Register command handlers."""
    bot.add_event_handler(handle_start, NewMessage(pattern=r"^/start$"))
    bot.add_event_handler(handle_help, NewMessage(pattern=r"^/help$"))
    logger.info("handler_registered")