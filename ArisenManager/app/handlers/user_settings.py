import re
from telethon import events
from ..user import profile_manager
from ..filters import group_filter

@group_filter
async def handle_user_settings(event: events.NewMessage.Event) -> None:
    message = event.message.message
    user = await event.get_sender()
    user_name = user.first_name or "دوست"
    
    # Initialize tables
    await profile_manager.init_tables()
    
    # Get user profile
    profile = await profile_manager.db_get_user_profile(event.chat_id, event.sender_id)
    user_lang = profile.get("lang", "fa") if profile else "fa"
    
    # Update first name
    if profile:
        await profile_manager.db_set_user_profile(event.chat_id, event.sender_id, {"first_name": user_name})
    
    # Show settings
    if re.search(r'تنظیمات من|my settings', message, re.IGNORECASE):
        if profile:
            if user_lang == "tr":
                summary = f"{user_name}, ayarlarınız:\n"
                if profile.get("lang"): summary += f"• Dil: {profile['lang']}\n"
                if profile.get("tone"): summary += f"• Ton: {profile['tone']}\n"
                if profile.get("humor_level"): summary += f"• Mizah: {profile['humor_level']}\n"
            else:
                summary = f"{user_name}، تنظیمات شما:\n"
                if profile.get("lang"): summary += f"• زبان: {profile['lang']}\n"
                if profile.get("tone"): summary += f"• لحن: {profile['tone']}\n"
                if profile.get("humor_level"): summary += f"• شوخی: {profile['humor_level']}\n"
                if profile.get("likes"):
                    likes = profile["likes"] if isinstance(profile["likes"], list) else profile["likes"].split(",")
                    summary += f"• سلیقهها: {', '.join(likes)}\n"
        else:
            summary = f"{user_name}، هنوز تنظیماتی ندارید."
        
        await event.respond(summary.strip(), reply_to=None)
        return
    
    # Language setting
    lang = profile_manager.parse_language(message)
    if lang and re.search(r'زبان من|my language', message, re.IGNORECASE):
        success = await profile_manager.db_set_user_profile(event.chat_id, event.sender_id, {"lang": lang, "first_name": user_name})
        if success:
            if lang == "tr":
                await event.respond(f"{user_name}, diliniz Türkçe olarak ayarlandı. 👍", reply_to=None)
            elif lang == "ku":
                await event.respond(f"{user_name}, زمانت بۆ کوردی دانرا. 👍", reply_to=None)
            else:
                await event.respond(f"{user_name}، زبانت روی فارسی تنظیم شد. 👍", reply_to=None)
        return
    
    # Tone setting
    tone = profile_manager.parse_tone(message)
    if tone and re.search(r'لحن من|my tone', message, re.IGNORECASE):
        success = await profile_manager.db_set_user_profile(event.chat_id, event.sender_id, {"tone": tone, "first_name": user_name})
        if success:
            if user_lang == "tr":
                await event.respond(f"{user_name}, tonunuz {tone} olarak ayarlandı.", reply_to=None)
            else:
                await event.respond(f"{user_name}، لحنت روی {tone} تنظیم شد.", reply_to=None)
        return
    
    # Humor setting
    humor = profile_manager.parse_humor(message)
    if humor and re.search(r'شوخی|humor', message, re.IGNORECASE):
        success = await profile_manager.db_set_user_profile(event.chat_id, event.sender_id, {"humor_level": humor, "first_name": user_name})
        if success:
            if user_lang == "tr":
                await event.respond(f"{user_name}, mizah seviyeniz {humor} olarak ayarlandı.", reply_to=None)
            else:
                await event.respond(f"{user_name}، سطح شوخیت روی {humor} تنظیم شد.", reply_to=None)
        return
    
    # Birthday setting
    birthday = profile_manager.parse_birthday(message)
    if birthday and re.search(r'تاریخ تولد|birthday', message, re.IGNORECASE):
        # Store pending confirmation
        profile_manager.pending_confirmations[event.sender_id] = {
            "type": "birthday",
            "value": birthday,
            "chat_id": event.chat_id,
            "user_name": user_name
        }
        
        if user_lang == "tr":
            await event.respond(f"{user_name}, doğum tarihinizi {birthday} olarak kaydetmeyi onaylıyor musunuz? (evet/hayır)", reply_to=None)
        else:
            await event.respond(f"{user_name}، برای ذخیره تاریخ تولد {birthday} تایید میکنی؟ (بله/خیر)", reply_to=None)
        return
    
    # Likes setting
    if re.search(r'سلیقه|likes', message, re.IGNORECASE):
        likes = profile_manager.parse_likes(message)
        if likes:
            success = await profile_manager.db_set_user_profile(event.chat_id, event.sender_id, {"likes": likes, "first_name": user_name})
            if success:
                if user_lang == "tr":
                    await event.respond(f"{user_name}, ilgi alanlarınız kaydedildi: {', '.join(likes)} 🎯", reply_to=None)
                else:
                    await event.respond(f"{user_name}، سلیقههات ذخیره شد: {', '.join(likes)} 🎯", reply_to=None)
        return
    
    # Handle confirmations
    if event.sender_id in profile_manager.pending_confirmations:
        confirmation = profile_manager.pending_confirmations[event.sender_id]
        
        if re.search(r'بله|yes|evet', message, re.IGNORECASE):
            if confirmation["type"] == "birthday":
                success = await profile_manager.db_set_user_profile(
                    confirmation["chat_id"], 
                    event.sender_id, 
                    {"birthday": confirmation["value"], "first_name": user_name}
                )
                if success:
                    if user_lang == "tr":
                        await event.respond(f"✅ {user_name}, doğum tarihiniz kaydedildi.", reply_to=None)
                    else:
                        await event.respond(f"✅ {user_name}، تاریخ تولدت ذخیره شد.", reply_to=None)
            
            del profile_manager.pending_confirmations[event.sender_id]
        
        elif re.search(r'خیر|no|hayır', message, re.IGNORECASE):
            del profile_manager.pending_confirmations[event.sender_id]
            if user_lang == "tr":
                await event.respond(f"{user_name}, işlem iptal edildi.", reply_to=None)
            else:
                await event.respond(f"{user_name}، عملیات لغو شد.", reply_to=None)

def register_user_settings_handlers(client) -> None:
    print("[DEBUG] Registering user settings handlers")
    client.add_event_handler(
        handle_user_settings,
        events.NewMessage(incoming=True)
    )
    print("[DEBUG] User settings handlers registered successfully")