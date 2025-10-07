from telethon import events, Button
from telethon.tl.functions.messages import ImportChatInviteRequest
from ..core.database import database
from ..core.clients import bot_clients
from ..utils.text_loader import text_loader
from ..utils.formatter import message_formatter
from ..filters import group_filter, sudo_filter

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
    print(f"[DEBUG] Group panel requested from chat: {event.chat_id}")
    
    if event.is_private:
        return
    
    user = await event.get_sender()
    chat = await event.get_chat()
    
    from telethon.tl.functions.channels import GetParticipantRequest
    try:
        participant = await event.client(GetParticipantRequest(event.chat_id, user.id))
        from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
        
        if not isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
            print(f"[DEBUG] User {user.id} is not admin")
            return
    except Exception as e:
        print(f"[DEBUG] Error checking admin status: {e}")
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
        rules_text = group_settings.get("rules_text") or text_loader.get_text("ui.rules.text")
        
        formatted_text = message_formatter.format_message(
            rules_text,
            chat=chat.title
        )
        
        await event.respond(formatted_text, parse_mode="markdown")
    else:
        disabled_text = text_loader.get_text("ui.rules.disabled")
        await event.respond(disabled_text)

import time
_processed_events = {}

async def handle_bot_added_to_group(event: events.ChatAction.Event) -> None:
    event_key = f"{event.chat_id}_{event.user_id}"
    current_time = time.time()
    
    print(f"[DEBUG] ChatAction triggered: event_key={event_key}, time={current_time}")
    
    if event_key in _processed_events:
        time_diff = current_time - _processed_events[event_key]
        print(f"[DEBUG] Event already processed {time_diff:.2f}s ago")
        if time_diff < 5:
            print(f"[DEBUG] Skipping duplicate event")
            return
    
    _processed_events[event_key] = current_time
    print(f"[DEBUG] Processing event: {event_key}")
    
    me = await event.client.get_me()
    
    if event.user_added and event.user_id == me.id and me.bot:
        print(f"[DEBUG] API Bot was added to group")
        chat = await event.get_chat()
        await database.add_group(event.chat_id, chat.title)
        
        from ..utils.config_loader import config_loader
        config = config_loader.get_telegram_config()
        sudo_id = config.get("sudo_id") or config.get("sudo")
        
        approval_text = text_loader.get_text("admin.group.approval_request", group_title=chat.title, group_id=event.chat_id)
        keyboard = [
            [Button.inline(text_loader.get_text("admin.button.approve"), f"approve_{event.chat_id}")],
            [Button.inline(text_loader.get_text("admin.button.reject"), f"reject_{event.chat_id}")]
        ]
        
        print(f"[DEBUG] Sending approval request to sudo: {sudo_id}")
        await bot_clients.apibot.send_message(sudo_id, approval_text, buttons=keyboard)
        print(f"[DEBUG] Approval request sent")
        
        pending_text = text_loader.get_text("ui.group.pending")
        print(f"[DEBUG] Sending pending message to group")
        await event.respond(pending_text)
        print(f"[DEBUG] Pending message sent")
    
    elif (event.user_added or event.user_joined) and event.user_id != me.id:
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

_processed_callbacks = {}

@sudo_filter
async def handle_group_approval(event: events.CallbackQuery.Event) -> None:
    data = event.data.decode()
    callback_key = f"{event.sender_id}_{data}"
    current_time = time.time()
    
    if callback_key in _processed_callbacks:
        time_diff = current_time - _processed_callbacks[callback_key]
        if time_diff < 5:
            print(f"[DEBUG] Callback {callback_key} already processed, skipping")
            return
    
    _processed_callbacks[callback_key] = current_time
    print(f"[DEBUG] Callback data: {data}")
    
    if data.startswith("approve_"):
        group_id = int(data.split("_")[1])
        print(f"[DEBUG] Approving group: {group_id}")
        await database.approve_group(group_id)
        
        approved_text = text_loader.get_text("ui.group.approved")
        print(f"[DEBUG] Sending approval message: {approved_text}")
        await bot_clients.apibot.send_message(group_id, approved_text)
        
        try:
            print(f"[DEBUG] Exporting invite link for group: {group_id}")
            from telethon.tl.functions.messages import ExportChatInviteRequest
            from telethon.errors import UserAlreadyParticipantError
            result = await bot_clients.apibot(ExportChatInviteRequest(group_id))
            invite_link = result.link
            print(f"[DEBUG] Invite link: {invite_link}")
            
            try:
                print(f"[DEBUG] Userbot joining via link")
                invite_hash = invite_link.split('/')[-1].replace('+', '')
                print(f"[DEBUG] Invite hash: {invite_hash}")
                await bot_clients.userbot(ImportChatInviteRequest(invite_hash))
                print(f"[DEBUG] Userbot joined successfully")
            except UserAlreadyParticipantError:
                print(f"[DEBUG] Userbot already in group")
            
            from telethon.tl.functions.channels import EditAdminRequest
            from telethon.tl.types import ChatAdminRights
            
            rights = ChatAdminRights(
                change_info=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                manage_call=True
            )
            
            userbot_id = (await bot_clients.userbot.get_me()).id
            print(f"[DEBUG] Making userbot admin: {userbot_id}")
            await bot_clients.apibot(EditAdminRequest(
                group_id,
                userbot_id,
                rights,
                ""
            ))
            print(f"[DEBUG] Userbot is now admin")
            
            success_text = text_loader.get_text("ui.group.userbot_added")
            print(f"[DEBUG] Sending success message: {success_text}")
            await bot_clients.apibot.send_message(group_id, success_text)
            
        except Exception as e:
            print(f"[DEBUG] Error occurred: {type(e).__name__}: {str(e)}")
            error_text = text_loader.get_text("err.group.userbot_failed", error=str(e))
            await bot_clients.apibot.send_message(group_id, error_text)
        
        print(f"[DEBUG] Editing and deleting approval message")
        await event.edit(text_loader.get_text("admin.group.approved"))
        await event.delete()
    
    elif data.startswith("reject_"):
        group_id = int(data.split("_")[1])
        print(f"[DEBUG] Rejecting group: {group_id}")
        await bot_clients.apibot.leave_chat(group_id)
        await event.edit(text_loader.get_text("admin.group.rejected"))
        await event.delete()

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
    
    print("[DEBUG] Group handlers registered successfully")
