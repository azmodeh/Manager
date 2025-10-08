from telethon import events, Button
from ..core.database import database
from ..utils.text_loader import text_loader
from ..filters import sudo_filter

@sudo_filter
async def handle_sudo_settings(event: events.CallbackQuery.Event) -> None:
    data = event.data.decode()
    
    if data == "sudo_settings":
        text = text_loader.get_text("admin.settings.main")
        buttons = [
            [Button.inline(text_loader.get_text("admin.settings.start"), "start_settings")],
            [Button.inline(text_loader.get_text("admin.settings.help"), "help_settings")],
            [Button.inline(text_loader.get_text("admin.button.back"), "back_main")]
        ]
        await event.edit(text, buttons=buttons)
    
    elif data == "start_settings":
        settings = await database.get_group_settings(0)
        status = text_loader.get_text("admin.status.enabled") if settings and settings.get("start_enabled") else text_loader.get_text("admin.status.disabled")
        
        text = text_loader.get_text("admin.settings.start.menu", status=status)
        buttons = [
            [Button.inline(text_loader.get_text("admin.button.toggle"), "toggle_start")],
            [Button.inline(text_loader.get_text("admin.button.edit_text"), "edit_start_text")],
            [Button.inline(text_loader.get_text("admin.button.back"), "sudo_settings")]
        ]
        await event.edit(text, buttons=buttons)
    
    elif data == "help_settings":
        settings = await database.get_group_settings(0)
        status = text_loader.get_text("admin.status.enabled") if settings and settings.get("help_enabled") else text_loader.get_text("admin.status.disabled")
        
        text = text_loader.get_text("admin.settings.help.menu", status=status)
        buttons = [
            [Button.inline(text_loader.get_text("admin.button.toggle"), "toggle_help")],
            [Button.inline(text_loader.get_text("admin.button.edit_text"), "edit_help_text")],
            [Button.inline(text_loader.get_text("admin.button.back"), "sudo_settings")]
        ]
        await event.edit(text, buttons=buttons)
    
    elif data == "toggle_start":
        settings = await database.get_group_settings(0) or {}
        new_status = not settings.get("start_enabled", False)
        await database.update_group_setting(0, "start_enabled", new_status)
        
        status = text_loader.get_text("admin.status.enabled") if new_status else text_loader.get_text("admin.status.disabled")
        text = text_loader.get_text("admin.settings.start.menu", status=status)
        buttons = [
            [Button.inline(text_loader.get_text("admin.button.toggle"), "toggle_start")],
            [Button.inline(text_loader.get_text("admin.button.edit_text"), "edit_start_text")],
            [Button.inline(text_loader.get_text("admin.button.back"), "sudo_settings")]
        ]
        await event.edit(text, buttons=buttons)
    
    elif data == "toggle_help":
        settings = await database.get_group_settings(0) or {}
        new_status = not settings.get("help_enabled", False)
        await database.update_group_setting(0, "help_enabled", new_status)
        
        status = text_loader.get_text("admin.status.enabled") if new_status else text_loader.get_text("admin.status.disabled")
        text = text_loader.get_text("admin.settings.help.menu", status=status)
        buttons = [
            [Button.inline(text_loader.get_text("admin.button.toggle"), "toggle_help")],
            [Button.inline(text_loader.get_text("admin.button.edit_text"), "edit_help_text")],
            [Button.inline(text_loader.get_text("admin.button.back"), "sudo_settings")]
        ]
        await event.edit(text, buttons=buttons)

def register_admin_handlers(client) -> None:
    print("[DEBUG] Registering admin handlers")
    client.add_event_handler(
        handle_sudo_settings,
        events.CallbackQuery()
    )
    print("[DEBUG] Admin handlers registered successfully")