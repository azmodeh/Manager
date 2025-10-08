from telethon import events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator

from ..core import bot_clients, database, text_loader
from ..filters import group_filter

async def handle_group_panel(event: events.NewMessage.Event) -> None:
    if event.is_private:
        return
    
    user = await event.get_sender()
    chat = await event.get_chat()
    
    try:
        participant = await event.client(GetParticipantRequest(event.chat_id, user.id))
        if not isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
            return
    except Exception:
        return
    
    text = text_loader.get_text("ui.group.panel", chat=chat.title)
    buttons = [
        [Button.inline(text_loader.get_text("ui.group.settings.welcome"), f"group_welcome_{event.chat_id}")],
        [Button.inline(text_loader.get_text("ui.group.settings.rules"), f"group_rules_{event.chat_id}")]
    ]
    
    await bot_clients.apibot.send_message(user.id, text, buttons=buttons)
    await event.respond(text_loader.get_text("ui.group.panel_sent"))

@group_filter
async def handle_rules_command(event: events.NewMessage.Event) -> None:
    group_settings = await database.get_group_settings(event.chat_id)
    
    if group_settings and group_settings.get("rules_enabled", False):
        chat = await event.get_chat()
        rules_text = group_settings.get("rules_text") or text_loader.get_text("ui.group.rules.default")
        formatted_text = rules_text.format(chat=chat.title)
        await event.respond(formatted_text)
    else:
        await event.respond(text_loader.get_text("ui.group.rules.disabled"))

async def handle_group_settings(event: events.CallbackQuery.Event) -> None:
    data = event.data.decode()
    
    if data.startswith("group_welcome_"):
        group_id = int(data.split("_")[2])
        settings = await database.get_group_settings(group_id)
        status = text_loader.get_text("admin.status.enabled") if settings and settings.get("welcome_enabled") else text_loader.get_text("admin.status.disabled")
        
        text = text_loader.get_text("ui.group.welcome.menu", status=status)
        buttons = [
            [Button.inline(text_loader.get_text("admin.button.toggle"), f"toggle_welcome_{group_id}")],
            [Button.inline(text_loader.get_text("admin.button.edit_text"), f"edit_welcome_{group_id}")],
            [Button.inline(text_loader.get_text("admin.button.back"), f"group_main_{group_id}")]
        ]
        await event.edit(text, buttons=buttons)
    
    elif data.startswith("group_rules_"):
        group_id = int(data.split("_")[2])
        settings = await database.get_group_settings(group_id)
        status = text_loader.get_text("admin.status.enabled") if settings and settings.get("rules_enabled") else text_loader.get_text("admin.status.disabled")
        
        text = text_loader.get_text("ui.group.rules.menu", status=status)
        buttons = [
            [Button.inline(text_loader.get_text("admin.button.toggle"), f"toggle_rules_{group_id}")],
            [Button.inline(text_loader.get_text("admin.button.edit_text"), f"edit_rules_{group_id}")],
            [Button.inline(text_loader.get_text("admin.button.back"), f"group_main_{group_id}")]
        ]
        await event.edit(text, buttons=buttons)
    
    elif data.startswith("toggle_welcome_"):
        group_id = int(data.split("_")[2])
        settings = await database.get_group_settings(group_id) or {}
        new_status = not settings.get("welcome_enabled", False)
        await database.update_group_setting(group_id, "welcome_enabled", new_status)
        
        status = text_loader.get_text("admin.status.enabled") if new_status else text_loader.get_text("admin.status.disabled")
        text = text_loader.get_text("ui.group.welcome.menu", status=status)
        buttons = [
            [Button.inline(text_loader.get_text("admin.button.toggle"), f"toggle_welcome_{group_id}")],
            [Button.inline(text_loader.get_text("admin.button.edit_text"), f"edit_welcome_{group_id}")],
            [Button.inline(text_loader.get_text("admin.button.back"), f"group_main_{group_id}")]
        ]
        await event.edit(text, buttons=buttons)
    
    elif data.startswith("toggle_rules_"):
        group_id = int(data.split("_")[2])
        settings = await database.get_group_settings(group_id) or {}
        new_status = not settings.get("rules_enabled", False)
        await database.update_group_setting(group_id, "rules_enabled", new_status)
        
        status = text_loader.get_text("admin.status.enabled") if new_status else text_loader.get_text("admin.status.disabled")
        text = text_loader.get_text("ui.group.rules.menu", status=status)
        buttons = [
            [Button.inline(text_loader.get_text("admin.button.toggle"), f"toggle_rules_{group_id}")],
            [Button.inline(text_loader.get_text("admin.button.edit_text"), f"edit_rules_{group_id}")],
            [Button.inline(text_loader.get_text("admin.button.back"), f"group_main_{group_id}")]
        ]
        await event.edit(text, buttons=buttons)
    
    elif data.startswith("group_main_"):
        group_id = int(data.split("_")[2])
        
        try:
            chat = await bot_clients.apibot.get_entity(group_id)
            chat_title = chat.title
        except Exception:
            chat_title = text_loader.get_text("ui.group.default_name")
        
        text = text_loader.get_text("ui.group.panel", chat=chat_title)
        buttons = [
            [Button.inline(text_loader.get_text("ui.group.settings.welcome"), f"group_welcome_{group_id}")],
            [Button.inline(text_loader.get_text("ui.group.settings.rules"), f"group_rules_{group_id}")]
        ]
        await event.edit(text, buttons=buttons)

def register_group_handlers(client) -> None:
    from .group_events import handle_bot_added_to_group, handle_group_approval, handle_new_chat_member
    
    client.add_event_handler(handle_group_panel, events.NewMessage(pattern=r'^(?:panel|پنل|settings|تنظیمات)$'))
    client.add_event_handler(handle_rules_command, events.NewMessage(pattern=r'^(?:rules|قوانین|قانون)$'))
    client.add_event_handler(handle_bot_added_to_group, events.ChatAction())
    client.add_event_handler(handle_group_approval, events.CallbackQuery())
    client.add_event_handler(handle_group_settings, events.CallbackQuery())
    client.add_event_handler(handle_new_chat_member, events.ChatAction())
