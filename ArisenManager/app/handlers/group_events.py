from typing import Dict
import time
from telethon import events, Button
from telethon.tl.functions.messages import ExportChatInviteRequest, ImportChatInviteRequest
from telethon.tl.functions.channels import EditAdminRequest
from telethon.tl.types import ChatAdminRights
from telethon.errors import UserAlreadyParticipantError

from ..core import bot_clients, database, text_loader
from ..utils.logger import logger
from ..filters import group_filter, sudo_filter
from ..utils.config_loader import config_loader

_processed_events: Dict[str, float] = {}
_processed_callbacks: Dict[str, float] = {}

@group_filter
async def handle_new_chat_member(event: events.ChatAction.Event) -> None:
    if event.user_added or event.user_joined:
        group_settings = await database.get_group_settings(event.chat_id)
        
        if group_settings and group_settings.get("welcome_enabled", False):
            await _send_welcome_message(event, group_settings)

async def handle_bot_added_to_group(event: events.ChatAction.Event) -> None:
    event_key = f"{event.chat_id}_{event.user_id}"
    current_time = time.time()
    
    if event_key in _processed_events:
        time_diff = current_time - _processed_events[event_key]
        if time_diff < 5:
            return
    
    _processed_events[event_key] = current_time
    me = await event.client.get_me()
    
    if event.user_added and event.user_id == me.id and me.bot:
        chat = await event.get_chat()
        await database.add_group(event.chat_id, chat.title)
        
        config = config_loader.get_telegram_config()
        sudo_id = config.get("sudo_id") or config.get("sudo")
        
        approval_text = text_loader.get_text("admin.group.approval_request", group_title=chat.title, group_id=event.chat_id)
        keyboard = [
            [Button.inline(text_loader.get_text("admin.button.approve"), f"approve_{event.chat_id}")],
            [Button.inline(text_loader.get_text("admin.button.reject"), f"reject_{event.chat_id}")]
        ]
        
        await bot_clients.apibot.send_message(sudo_id, approval_text, buttons=keyboard)
        await event.respond(text_loader.get_text("ui.group.pending"))
    
    elif (event.user_added or event.user_joined) and event.user_id != me.id:
        group_settings = await database.get_group_settings(event.chat_id)
        
        if group_settings and group_settings.get("welcome_enabled", False):
            await _send_welcome_message(event, group_settings)

@sudo_filter
async def handle_group_approval(event: events.CallbackQuery.Event) -> None:
    data = event.data.decode()
    callback_key = f"{event.sender_id}_{data}"
    current_time = time.time()
    
    if callback_key in _processed_callbacks:
        time_diff = current_time - _processed_callbacks[callback_key]
        if time_diff < 5:
            return
    
    _processed_callbacks[callback_key] = current_time
    
    if data.startswith("approve_"):
        group_id = int(data.split("_")[1])
        await database.approve_group(group_id)
        
        await bot_clients.apibot.send_message(group_id, text_loader.get_text("ui.group.approved"))
        
        try:
            await _setup_userbot_in_group(group_id)
        except Exception as e:
            error_text = text_loader.get_text("err.group.userbot_failed", error=str(e))
            await bot_clients.apibot.send_message(group_id, error_text)
        
        await event.edit(text_loader.get_text("admin.group.approved"))
        await event.delete()
    
    elif data.startswith("reject_"):
        group_id = int(data.split("_")[1])
        await database.reject_group(group_id)
        
        await bot_clients.apibot.send_message(group_id, text_loader.get_text("ui.group.rejected"))
        await event.edit(text_loader.get_text("admin.group.rejected"))
        await event.delete()

async def _setup_userbot_in_group(group_id: int) -> None:
    result = await bot_clients.apibot(ExportChatInviteRequest(group_id))
    invite_link = result.link
    
    try:
        invite_hash = invite_link.split('/')[-1].replace('+', '')
        await bot_clients.userbot(ImportChatInviteRequest(invite_hash))
    except UserAlreadyParticipantError:
        pass
    
    rights = ChatAdminRights(
        change_info=True,
        delete_messages=True,
        ban_users=True,
        invite_users=True,
        pin_messages=True,
        manage_call=True
    )
    
    userbot_id = (await bot_clients.userbot.get_me()).id
    await bot_clients.apibot(EditAdminRequest(group_id, userbot_id, rights, ""))
    await bot_clients.apibot.send_message(group_id, text_loader.get_text("ui.group.userbot_added"))

async def _send_welcome_message(event: events.ChatAction.Event, group_settings: dict) -> None:
    user = await event.get_user()
    chat = await event.get_chat()
    
    welcome_text = group_settings.get("welcome_text") or text_loader.get_text("ui.welcome.text")
    formatted_text = welcome_text.format(user=user.first_name, chat=chat.title)
    
    await event.respond(formatted_text)