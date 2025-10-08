from telethon import events, Button
from telethon.tl.functions.messages import ImportChatInviteRequest, ExportChatInviteRequest
from telethon.tl.functions.channels import GetParticipantRequest, EditAdminRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator, ChatAdminRights
from telethon.errors import UserAlreadyParticipantError
import logging
import time
from ..core.database import database
from ..core.clients import bot_clients
from ..utils.text_loader import text_loader
from ..utils.formatter import message_formatter
from ..utils.config_loader import config_loader
from ..filters import group_filter, sudo_filter

logger = logging.getLogger(__name__)

@group_filter
async def handle_new_chat_member(event: events.ChatAction.Event) -> None:
    if event.user_added or event.user_joined:
        group_settings = await database.get_group_settings(event.chat_id)
        
        if group_settings and group_settings.get("welcome_enabled", False):
            user = await event.get_user()
            chat = await event.get_chat()
            
            welcome_text = group_settings.get("welcome_text") or text_loader.get_text("ui.welcome.text")
            formatted_text = message_formatter.format_message(
                welcome_text,
                user=user.first_name,
                chat=chat.title
            )
            
            await event.respond(formatted_text, parse_mode="markdown")

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
    
    await bot_clients.apibot.send_message(user.id, text, buttons=buttons, parse_mode="markdown")
    await event.respond(text_loader.get_text("ui.group.panel_sent"), reply_to=None)

@group_filter
async def handle_rules_command(event: events.NewMessage.Event) -> None:
    group_settings = await database.get_group_settings(event.chat_id)
    
    if group_settings and group_settings.get("rules_enabled", False):
        chat = await event.get_chat()
        rules_text = group_settings.get("rules_text") or text_loader.get_text("ui.rules.text")
        
        formatted_text = message_formatter.format_message(
            rules_text,
            chat=chat.title
        )
        
        await event.respond(formatted_text, parse_mode="markdown", reply_to=None)
    else:
        disabled_text = text_loader.get_text("ui.rules.disabled")
        await event.respond(disabled_text, reply_to=None)

_processed_events = {}
_processed_callbacks = {}

async def _send_welcome_message(event: events.ChatAction.Event, group_settings: dict) -> None:
    """Helper function to send welcome message"""
    user = await event.get_user()
    chat = await event.get_chat()
    
    welcome_text = group_settings.get("welcome_text") or text_loader.get_text("ui.welcome.text")
    formatted_text = message_formatter.format_message(
        welcome_text,
        user=user.first_name,
        chat=chat.title
    )
    
    await event.respond(formatted_text, parse_mode="markdown")

async def handle_bot_added_to_group(event: events.ChatAction.Event) -> None:
    event_key = f"{event.chat_id}_{event.user_id}"
    current_time = time.time()
    
    logger.debug(f"ChatAction triggered: event_key={event_key}, time={current_time}")
    
    if event_key in _processed_events:
        time_diff = current_time - _processed_events[event_key]
        logger.debug(f"Event already processed {time_diff:.2f}s ago")
        if time_diff < 5:
            logger.debug("Skipping duplicate event")
            return
    
    _processed_events[event_key] = current_time
    logger.debug(f"Processing event: {event_key}")
    
    me = await event.client.get_me()
    
    if event.user_added and event.user_id == me.id and me.bot:
        logger.info("API Bot was added to group")
        chat = await event.get_chat()
        await database.add_group(event.chat_id, chat.title)
        
        config = config_loader.get_telegram_config()
        sudo_id = config.get("sudo_id") or config.get("sudo")
        
        approval_text = text_loader.get_text("admin.group.approval_request", group_title=chat.title, group_id=event.chat_id)
        keyboard = [
            [Button.inline(text_loader.get_text("admin.button.approve"), f"approve_{event.chat_id}")],
            [Button.inline(text_loader.get_text("admin.button.reject"), f"reject_{event.chat_id}")]
        ]
        
        logger.debug(f"Sending approval request to sudo: {sudo_id}")
        await bot_clients.apibot.send_message(sudo_id, approval_text, buttons=keyboard)
        logger.debug("Approval request sent")
        
        pending_text = text_loader.get_text("ui.group.pending")
        logger.debug("Sending pending message to group")
        await event.respond(pending_text)
        logger.debug("Pending message sent")
    
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
            logger.debug(f"Callback {callback_key} already processed, skipping")
            return
    
    _processed_callbacks[callback_key] = current_time
    logger.debug(f"Callback data: {data}")
    
    if data.startswith("approve_"):
        group_id = int(data.split("_")[1])
        logger.info(f"Approving group: {group_id}")
        await database.approve_group(group_id)
        
        approved_text = text_loader.get_text("ui.group.approved")
        logger.debug(f"Sending approval message: {approved_text}")
        await bot_clients.apibot.send_message(group_id, approved_text)
        
        try:
            await _setup_userbot_in_group(group_id)
            
        except Exception as e:
            logger.error(f"Error occurred: {type(e).__name__}: {str(e)}")
            error_text = text_loader.get_text("err.group.userbot_failed", error=str(e))
            await bot_clients.apibot.send_message(group_id, error_text)
        
        logger.debug("Editing and deleting approval message")
        await event.edit(text_loader.get_text("admin.group.approved"))
        await event.delete()
    
    elif data.startswith("reject_"):
        group_id = int(data.split("_")[1])
        logger.info(f"Rejecting group: {group_id}")
        await database.reject_group(group_id)
        
        rejected_text = text_loader.get_text("ui.group.rejected")
        await bot_clients.apibot.send_message(group_id, rejected_text)
        
        await event.edit(text_loader.get_text("admin.group.rejected"))
        await event.delete()

async def _setup_userbot_in_group(group_id: int) -> None:
    """Helper function to setup userbot in approved group"""
    logger.debug(f"Exporting invite link for group: {group_id}")
    result = await bot_clients.apibot(ExportChatInviteRequest(group_id))
    invite_link = result.link
    logger.debug(f"Invite link: {invite_link}")
    
    try:
        logger.debug("Userbot joining via link")
        invite_hash = invite_link.split('/')[-1].replace('+', '')
        logger.debug(f"Invite hash: {invite_hash}")
        await bot_clients.userbot(ImportChatInviteRequest(invite_hash))
        logger.debug("Userbot joined successfully")
    except UserAlreadyParticipantError:
        logger.debug("Userbot already in group")
    
    rights = ChatAdminRights(
        change_info=True,
        delete_messages=True,
        ban_users=True,
        invite_users=True,
        pin_messages=True,
        manage_call=True
    )
    
    userbot_id = (await bot_clients.userbot.get_me()).id
    logger.debug(f"Making userbot admin: {userbot_id}")
    await bot_clients.apibot(EditAdminRequest(
        group_id,
        userbot_id,
        rights,
        ""
    ))
    logger.debug("Userbot is now admin")
    
    success_text = text_loader.get_text("ui.group.userbot_added")
    logger.debug(f"Sending success message: {success_text}")
    await bot_clients.apibot.send_message(group_id, success_text)up_id}")
        await bot_clients.apibot.leave_chat(group_id)
        await event.edit(text_loader.get_text("admin.group.rejected"))
        await event.delete()

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
        
        # Get group info
        try:
            chat = await bot_clients.apibot.get_entity(group_id)
            chat_title = chat.title
        except Exception:
            chat_title = "گروه"
        
        text = text_loader.get_text("ui.group.panel", chat=chat_title)
        buttons = [
            [Button.inline(text_loader.get_text("ui.group.settings.welcome"), f"group_welcome_{group_id}")],
            [Button.inline(text_loader.get_text("ui.group.settings.rules"), f"group_rules_{group_id}")]
        ]
        await event.edit(text, buttons=buttons)

def register_group_handlers(client) -> None:
    print("[DEBUG] Registering group handlers")
    
    client.add_event_handler(
        handle_group_panel,
        events.NewMessage(pattern=r'^(?:panel|پنل|settings|تنظیمات)$', incoming=True)
    )
    
    client.add_event_handler(
        handle_rules_command,
        events.NewMessage(pattern=r'^(?:rules|قوانین|قانون)$', incoming=True)
    )
    
    client.add_event_handler(
        handle_bot_added_to_group,
        events.ChatAction()
    )
    
    client.add_event_handler(
        handle_group_approval,
        events.CallbackQuery()
    )
    
    client.add_event_handler(
        handle_group_settings,
        events.CallbackQuery()
    )
    
    print("[DEBUG] Group handlers registered successfully")
