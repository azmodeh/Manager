from telethon import events
from ..core.database import database
from ..utils.text_loader import text_loader
from ..filters import sudo_filter

_editing_sessions = {}

@sudo_filter
async def handle_text_editing(event: events.CallbackQuery.Event) -> None:
    data = event.data.decode()
    
    if data == "edit_start_text":
        _editing_sessions[event.sender_id] = {"type": "start", "group_id": 0}
        text = text_loader.get_text("admin.edit.start_prompt")
        await event.edit(text)
    
    elif data == "edit_help_text":
        _editing_sessions[event.sender_id] = {"type": "help", "group_id": 0}
        text = text_loader.get_text("admin.edit.help_prompt")
        await event.edit(text)
    
    elif data.startswith("edit_welcome_"):
        group_id = int(data.split("_")[2])
        _editing_sessions[event.sender_id] = {"type": "welcome", "group_id": group_id}
        text = text_loader.get_text("admin.edit.welcome_prompt")
        await event.edit(text)
    
    elif data.startswith("edit_rules_"):
        group_id = int(data.split("_")[2])
        _editing_sessions[event.sender_id] = {"type": "rules", "group_id": group_id}
        text = text_loader.get_text("admin.edit.rules_prompt")
        await event.edit(text)

@sudo_filter
async def handle_text_input(event: events.NewMessage.Event) -> None:
    if event.sender_id not in _editing_sessions:
        return
    
    session = _editing_sessions[event.sender_id]
    new_text = event.message.message
    
    field_name = f"{session['type']}_text"
    await database.update_group_setting(session["group_id"], field_name, new_text)
    
    success_text = text_loader.get_text("admin.edit.success", type=session["type"])
    await event.respond(success_text, reply_to=None)
    
    del _editing_sessions[event.sender_id]

def register_text_editor_handlers(client) -> None:
    print("[DEBUG] Registering text editor handlers")
    client.add_event_handler(
        handle_text_editing,
        events.CallbackQuery()
    )
    
    client.add_event_handler(
        handle_text_input,
        events.NewMessage(incoming=True)
    )
    print("[DEBUG] Text editor handlers registered successfully")