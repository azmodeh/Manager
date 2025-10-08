from telethon import events, Button
from typing import List
from ..core.database import database
from ..utils.text_loader import text_loader
from ..utils.formatter import message_formatter
from ..filters import private_filter, sudo_filter

async def handle_start(event: events.NewMessage.Event) -> None:
    user = await event.get_sender()
    settings = await database.get_group_settings(0)
    
    if settings and settings.get(text_loader.get_text("sys.start_enabled_key"), False):
        start_text = settings.get(text_loader.get_text("sys.start_text_key")) or text_loader.get_text("ui.start.text")
        formatted_text = message_formatter.format_message(start_text, user=user.first_name)
        await event.respond(formatted_text, parse_mode=text_loader.get_text("sys.markdown_mode"), reply_to=None)
    else:
        await event.respond(text_loader.get_text("ui.start.disabled"), reply_to=None)

async def handle_help(event: events.NewMessage.Event) -> None:
    settings = await database.get_group_settings(0)
    
    if settings and settings.get(text_loader.get_text("sys.help_enabled_key"), False):
        help_text = settings.get(text_loader.get_text("sys.help_text_key")) or text_loader.get_text("ui.help.text")
        formatted_text = message_formatter.format_message(help_text)
        await event.respond(formatted_text, parse_mode=text_loader.get_text("sys.markdown_mode"), reply_to=None)
    else:
        await event.respond(text_loader.get_text("ui.help.disabled"), reply_to=None)

@sudo_filter
async def handle_sudo_panel(event: events.NewMessage.Event) -> None:
    buttons = [
        [Button.inline(text_loader.get_text("admin.settings"), text_loader.get_text("sys.sudo_settings_callback"))]
    ]
    
    await event.respond(text_loader.get_text("admin.panel"), buttons=buttons)

def register_start_help_handlers(client) -> None:
    client.add_event_handler(
        private_filter(handle_start),
        events.NewMessage(pattern=text_loader.get_text("sys.start_pattern"), incoming=True)
    )
    
    client.add_event_handler(
        private_filter(handle_help),
        events.NewMessage(pattern=text_loader.get_text("sys.help_pattern"), incoming=True)
    )
    
    client.add_event_handler(
        handle_sudo_panel,
        events.NewMessage(pattern=text_loader.get_text("sys.admin_pattern"), incoming=True)
    )