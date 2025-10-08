import re
from telethon import events
from ..ai import ai_client
from ..ai.personality import personality
from ..memory import vector_memory
from ..filters import group_filter
from ..utils.text_loader import text_loader
from ..utils.logger import logger

@group_filter
async def handle_ai_social(event: events.NewMessage.Event) -> None:
    logger.info(f"AI handler triggered for message: {event.message.message[:50]}...")
    
    message = event.message.message
    user = await event.get_sender()
    user_name = personality.get_user_name(user)
    
    logger.info(f"User: {user_name}, Message: {message}")
    
    # Check if should respond
    is_mention = any(keyword in message.lower() for keyword in ["جمی", "jemm", "jemi"])
    is_reply = event.message.reply_to is not None
    
    logger.info(f"Is mention: {is_mention}, Is reply: {is_reply}")
    
    should_respond = personality.should_respond(message, event.sender_id, is_reply, is_mention)
    logger.info(f"Should respond: {should_respond}")
    
    if not should_respond:
        logger.info("Not responding - conditions not met")
        return
    
    # Get conversation context from memory
    chat_context = []  # Disabled for now
    
    # Build context-aware prompt
    logger.info("Building context prompt...")
    context_prompt = personality.build_context_prompt(message, user_name, chat_context)
    logger.info(f"Context prompt built: {context_prompt[:100]}...")
    
    # Generate response
    logger.info("Generating AI response...")
    try:
        response = await ai_client.generate_response(context_prompt, event.chat_id, event.sender_id)
        logger.info(f"AI response received: {response[:100]}...")
    except Exception as e:
        logger.error(f"AI response generation failed: {e}")
        await event.respond("⚠️ سیستم هوش مصنوعی فعلاً در دسترس نیست، لطفاً بعداً دوباره امتحان کنید.")
        return
    
    # Clean response (remove prefix/suffix if present)
    clean_response = response.replace("🤖 **جمی:** ", "").replace("✨", "").strip()
    logger.info(f"Cleaned response: {clean_response[:100]}...")
    
    # Send response
    logger.info("Sending response...")
    await event.respond(clean_response, parse_mode="markdown", reply_to=None)
    logger.info("Response sent successfully")
    
    # Update personality tracking
    personality.update_user_interaction(event.sender_id, user_name, message, clean_response)
    
    # Store in vector memory (if available)
    try:
        # Note: This would need actual embedding generation
        pass
    except Exception:
        pass

# Removed - integrated into handle_ai_social

def register_ai_handlers(client) -> None:
    client.add_event_handler(
        handle_ai_social,
        events.NewMessage(incoming=True)
    )
    logger.info(text_loader.get_text("log.handlers.ai_registered"))