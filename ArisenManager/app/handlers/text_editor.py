from telethon import events
from ..core.database import database
from ..utils.text_loader import text_loader
from ..filters import sudo_filter
from typing import Dict, Any

_editing_sessions: Dict[int, Dict[str, Any]] = {}

_EDIT_HANDLERS = {
    "edit_start_text": ("start", 0, "admin.edit.start_prompt"),
    "edit_help_text": ("help", 0, "admin.edit.help_prompt")
}

@sudo_filter
async def handle_text_editing(event: events.CallbackQuery.Event) -> None:
    data = event.data.decode()
    
    if data in _EDIT_HANDLERS:
        edit_type, group_id, prompt_key = _EDIT_HANDLERS[data]
        _editing_sessions[event.sender_id] = {"type": edit_type, "group_id": group_id}
        await event.edit(text_loader.get_text(prompt_key))
    elif data.startswith(("edit_welcome_", "edit_rules_")):
        parts = data.split("_")
        edit_type, group_id = parts[1], int(parts[2])
        _editing_sessions[event.sender_id] = {"type": edit_type, "group_id": group_id}
        await event.edit(text_loader.get_text(f"admin.edit.{edit_type}_prompt"))

@sudo_filter
async def handle_text_input(event: events.NewMessage.Event) -> None:
    session = _editing_sessions.pop(event.sender_id, None)
    if not session:
        return
    
    await database.update_group_setting(
        session["group_id"], 
        f"{session['type']}_text", 
        event.message.message
    )
    
    await event.respond(
        text_loader.get_text("admin.edit.success", type=session["type"]),
        reply_to=None
    )

def register_text_editor_handlers(client) -> None:
    client.add_event_handler(handle_text_editing, events.CallbackQuery())
    client.add_event_handler(handle_text_input, events.NewMessage(incoming=True))