from telethon import events, Button
from typing import List
from ..core.database import database
from ..utils.text_loader import text_loader
from ..utils.formatter import message_formatter
from ..filters import private_filter, sudo_filter

async def handle_start(event: events.NewMessage.Event) -> None:
    user = await event.get_sender()
    settings = await database.get_group_settings(0)
    
    if settings and settings.get("start_enabled", False):
        start_text = settings.get("start_text") or text_loader.get_text("ui.start.text")
        formatted_text = message_formatter.format_message(start_text, user=user.first_name)
        await event.respond(formatted_text, parse_mode="markdown", reply_to=None)
    else:
        disabled_text = text_loader.get_text("ui.start.disabled")
        await event.respond(disabled_text, reply_to=None)

async def handle_help(event: events.NewMessage.Event) -> None:
    settings = await database.get_group_settings(0)
    
    if settings and settings.get("help_enabled", False):
        help_text = settings.get("help_text") or text_loader.get_text("ui.help.text")
        formatted_text = message_formatter.format_message(help_text)
        await event.respond(formatted_text, parse_mode="markdown", reply_to=None)
    else:
        disabled_text = text_loader.get_text("ui.help.disabled")
        await event.respond(disabled_text, reply_to=None)

@sudo_filter
async def handle_sudo_panel(event: events.NewMessage.Event) -> None:
    print(f"[DEBUG] Sudo panel requested by user: {event.sender_id}")
    text = text_loader.get_text("admin.panel")
    
    buttons = [
        [Button.inline(text_loader.get_text("admin.settings"), "sudo_settings")]
    ]
    
    await event.respond(text, buttons=buttons)

def register_start_help_handlers(client) -> None:
    print("[DEBUG] Registering start/help handlers")
    client.add_event_handler(
        private_filter(handle_start),
        events.NewMessage(pattern=r'^(?:start|استارت|شروع)$', incoming=True)
    )
    
    client.add_event_handler(
        private_filter(handle_help),
        events.NewMessage(pattern=r'^(?:help|هلپ|راهنما|کمک)$', incoming=True)
    )
    
    client.add_event_handler(
        handle_sudo_panel,
        events.NewMessage(pattern=r'^(?:panel|پنل|admin|ادمین)$', incoming=True)
    )
    
    print("[DEBUG] Start/Help handlers registered successfully")