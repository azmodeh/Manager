import re
from typing import Dict, Any, Optional
from telethon import events
from ..user import profile_manager
from ..filters import group_filter
from ..utils.text_loader import text_loader

# Cache frequently used text keys
class TextKeys:
    def __init__(self) -> None:
        # System field keys
        self.lang_field = "lang"
        self.first_name_field = "first_name"
        self.tone_field = "tone"
        self.humor_level_field = "humor_level"
        self.birthday_field = "birthday"
        self.likes_field = "likes"
        
        # System keys for confirmations
        self.type_key = "type"
        self.value_key = "value"
        self.chat_id_key = "chat_id"
        self.user_name_key = "user_name"
        self.birthday_type = "birthday"
        
        # Regex patterns
        self.settings_pattern = r"تنظیمات|settings"
        self.language_pattern = r"زبان|language|lang"
        self.tone_pattern = r"لحن|tone"
        self.humor_pattern = r"طنز|humor"
        self.birthday_pattern = r"تولد|birthday"
        self.likes_pattern = r"علاقه|likes?"
        self.yes_pattern = r"بله|yes|آره"
        self.no_pattern = r"نه|no|خیر"

text_keys = TextKeys()

@group_filter
async def handle_user_settings(event: events.NewMessage.Event) -> None:
    message = event.message.message
    user = await event.get_sender()
    user_name = user.first_name or text_loader.get_text("ui.default_user_name")
    
    await profile_manager.init_tables()
    profile = await profile_manager.db_get_user_profile(event.chat_id, event.sender_id)
    user_lang = profile.get(text_keys.lang_field, "fa") if profile else "fa"
    
    # Update first name if profile exists
    if profile:
        await profile_manager.db_set_user_profile(event.chat_id, event.sender_id, {text_keys.first_name_field: user_name})
    
    # Show settings
    if re.search(text_keys.settings_pattern, message, re.IGNORECASE):
        if profile:
            summary = text_loader.get_text("ui.settings_summary", user=user_name, lang=user_lang)
            
            # Build settings display efficiently
            settings_map = [
                (text_keys.lang_field, "ui.setting_lang"),
                (text_keys.tone_field, "ui.setting_tone"),
                (text_keys.humor_level_field, "ui.setting_humor")
            ]
            
            for field, text_key in settings_map:
                if profile.get(field):
                    summary += text_loader.get_text(text_key, value=profile[field], lang=user_lang)
            
            # Handle likes separately due to list processing
            if profile.get(text_keys.likes_field):
                likes_value = profile[text_keys.likes_field]
                likes = likes_value if isinstance(likes_value, list) else likes_value.split(",")
                summary += text_loader.get_text("ui.setting_likes", value=', '.join(likes), lang=user_lang)
        else:
            summary = text_loader.get_text("ui.no_settings", user=user_name, lang=user_lang)
        
        await event.respond(summary.strip(), reply_to=None)
        return
    
    # Handle setting updates with consolidated logic
    async def update_setting(field: str, value: str, pattern: str, response_key: str, **kwargs) -> bool:
        if value and re.search(pattern, message, re.IGNORECASE):
            updates = {field: value, text_keys.first_name_field: user_name}
            success = await profile_manager.db_set_user_profile(event.chat_id, event.sender_id, updates)
            if success:
                await event.respond(text_loader.get_text(response_key, user=user_name, lang=user_lang, **kwargs), reply_to=None)
            return True
        return False
    
    # Process settings in order
    settings_checks = [
        (text_keys.lang_field, profile_manager.parse_language(message), text_keys.language_pattern, "ui.lang_set", {"lang": profile_manager.parse_language(message) or ""}),
        (text_keys.tone_field, profile_manager.parse_tone(message), text_keys.tone_pattern, "ui.tone_set", {"tone": profile_manager.parse_tone(message) or ""}),
        (text_keys.humor_level_field, profile_manager.parse_humor(message), text_keys.humor_pattern, "ui.humor_set", {"humor": profile_manager.parse_humor(message) or ""})
    ]
    
    for field, value, pattern, response_key, extra_kwargs in settings_checks:
        if await update_setting(field, value, pattern, response_key, **extra_kwargs):
            return
    
    # Birthday setting with confirmation
    birthday = profile_manager.parse_birthday(message)
    if birthday and re.search(text_keys.birthday_pattern, message, re.IGNORECASE):
        profile_manager.pending_confirmations[event.sender_id] = {
            text_keys.type_key: text_keys.birthday_type,
            text_keys.value_key: birthday,
            text_keys.chat_id_key: event.chat_id,
            text_keys.user_name_key: user_name
        }
        await event.respond(text_loader.get_text("ui.birthday_confirm", user=user_name, birthday=birthday, lang=user_lang), reply_to=None)
        return
    
    # Likes setting
    if re.search(text_keys.likes_pattern, message, re.IGNORECASE):
        likes = profile_manager.parse_likes(message)
        if likes:
            updates = {text_keys.likes_field: likes, text_keys.first_name_field: user_name}
            success = await profile_manager.db_set_user_profile(event.chat_id, event.sender_id, updates)
            if success:
                await event.respond(text_loader.get_text("ui.likes_saved", user=user_name, likes=', '.join(likes), lang=user_lang), reply_to=None)
        return
    
    # Handle confirmations
    if event.sender_id in profile_manager.pending_confirmations:
        confirmation = profile_manager.pending_confirmations[event.sender_id]
        
        if re.search(text_keys.yes_pattern, message, re.IGNORECASE):
            if confirmation[text_keys.type_key] == text_keys.birthday_type:
                updates = {
                    text_keys.birthday_field: confirmation[text_keys.value_key],
                    text_keys.first_name_field: user_name
                }
                success = await profile_manager.db_set_user_profile(
                    confirmation[text_keys.chat_id_key], event.sender_id, updates
                )
                if success:
                    await event.respond(text_loader.get_text("ui.birthday_saved", user=user_name, lang=user_lang), reply_to=None)
            
            del profile_manager.pending_confirmations[event.sender_id]
        
        elif re.search(text_keys.no_pattern, message, re.IGNORECASE):
            del profile_manager.pending_confirmations[event.sender_id]
            await event.respond(text_loader.get_text("ui.operation_cancelled", user=user_name, lang=user_lang), reply_to=None)

def register_user_settings_handlers(client) -> None:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(text_loader.get_text("log.registering_handlers", handler="user_settings"))
    client.add_event_handler(handle_user_settings, events.NewMessage(incoming=True))
    logger.info(text_loader.get_text("log.handlers_registered", handler="user_settings"))