from telethon import events, Button
from ..core.database import database
from ..utils.text_loader import text_loader
from ..utils.keyboard_builder import keyboard_builder
from ..filters import sudo_filter

@sudo_filter
async def handle_admin_callback(event: events.CallbackQuery.Event) -> None:
    data = event.data.decode()
    
    if data == "admin_general":
        text = text_loader.get_text("admin.settings")
        keyboard = [
            [Button.inline("✅ فعال کردن استارت", "enable_start")],
            [Button.inline("❌ غیرفعال کردن استارت", "disable_start")],
            [Button.inline("✅ فعال کردن هلپ", "enable_help")],
            [Button.inline("❌ غیرفعال کردن هلپ", "disable_help")],
            [Button.inline("🔙 بازگشت", "back_main")]
        ]
        await event.edit(text, buttons=keyboard)
    
    elif data == "enable_start":
        await database.update_group_setting(0, "start_enabled", True)
        await event.answer(text_loader.get_text("ui.start.title") + " فعال شد", alert=True)
    
    elif data == "disable_start":
        await database.update_group_setting(0, "start_enabled", False)
        await event.answer(text_loader.get_text("ui.start.title") + " غیرفعال شد", alert=True)
    
    elif data == "enable_help":
        await database.update_group_setting(0, "help_enabled", True)
        await event.answer(text_loader.get_text("ui.help.title") + " فعال شد", alert=True)
    
    elif data == "disable_help":
        await database.update_group_setting(0, "help_enabled", False)
        await event.answer(text_loader.get_text("ui.help.title") + " غیرفعال شد", alert=True)
    
    elif data == "back_main":
        text = text_loader.get_text("admin.panel")
        keyboard = keyboard_builder.build_from_template("admin_panel")
        
        buttons = []
        for row in keyboard:
            button_row = []
            for btn in row:
                button_row.append(Button.inline(btn["text"], btn["callback_data"]))
            buttons.append(button_row)
        
        await event.edit(text, buttons=buttons)

_handlers_registered = False

def register_admin_handlers(client) -> None:
    global _handlers_registered
    if _handlers_registered:
        print("[DEBUG] Admin handlers already registered, skipping")
        return
    
    print("[DEBUG] Registering admin handlers")
    client.add_event_handler(
        handle_admin_callback,
        events.CallbackQuery()
    )
    
    _handlers_registered = True
    print("[DEBUG] Admin handlers registered successfully")