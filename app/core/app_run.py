import asyncio
from app.core.logger import setup_logging, MessageLogger
from app.core.clients import ClientManager
from app.core.db import init_db
from app.handlers.commands import register_handlers as register_commands
from app.handlers.rules_welcome import register_handlers as register_rules
from app.handlers.admin_panel import register_handlers as register_panel
from app.handlers.group_approval import register_handlers as register_approval
from app.handlers.userbot_commands import register_handlers as register_userbot
from app.handlers.approval_callbacks import register_handlers as register_callbacks
from app.handlers.reload_handler import register_handlers as register_reload
from app.core.app_context import AppContext
from app.services.notifier import NotificationService

logger = MessageLogger(__name__)


async def start_clients() -> None:
    """Start Telegram clients and register handlers."""
    client_manager = ClientManager()
    userbot, bot = client_manager.get_clients()
    
    notification_service = NotificationService()
    
    phone = client_manager.config["telegram"].get("phone_number")
    if phone:
        await userbot.start(phone)  # type: ignore
    else:
        await userbot.start()  # type: ignore
    await bot.start(bot_token=client_manager.config["telegram"]["bot_token"])  # type: ignore
    
    # Set global context
    AppContext.set_clients(userbot, bot)
    
    register_commands(userbot, bot)
    register_rules(userbot, bot)
    register_panel(userbot, bot)
    register_approval(userbot, bot)
    register_userbot(userbot, bot)
    register_callbacks(userbot, bot)
    register_reload(userbot, bot)
    
    await notification_service.notify_userbot_online(userbot)
    await notification_service.notify_bot_online(bot)
    
    await userbot.run_until_disconnected()  # type: ignore


async def main() -> None:
    """Main async function."""
    setup_logging()
    await init_db()
    logger.info("database_connected")
    await start_clients()


def run_application() -> None:
    """Main application entry point."""
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(
            asyncio.WindowsSelectorEventLoopPolicy()
        )
    asyncio.run(main())