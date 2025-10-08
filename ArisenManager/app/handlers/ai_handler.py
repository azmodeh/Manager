import re
from telethon import events
from ..ai import ai_client
from ..ai.personality import personality
from ..memory import vector_memory
from ..filters import group_filter

@group_filter
async def handle_ai_social(event: events.NewMessage.Event) -> None:
    message = event.message.message
    user = await event.get_sender()
    user_name = personality.get_user_name(user)
    
    # Check if should respond
    is_mention = any(keyword in message.lower() for keyword in ["جمی", "jemm", "jemi"])
    is_reply = event.message.reply_to is not None
    
    if not personality.should_respond(message, event.sender_id, is_reply, is_mention):
        return
    
    # Get conversation context from memory
    try:
        await vector_memory.init()
        context_results = await vector_memory.get_context(
            group_id=event.chat_id,
            user_id=event.sender_id,
            top_k=3
        )
        chat_context = [result.text for result in context_results]
    except Exception:
        chat_context = []
    
    # Build context-aware prompt
    context_prompt = personality.build_context_prompt(message, user_name, chat_context)
    
    # Generate response
    response = await ai_client.generate_response(context_prompt, event.chat_id, event.sender_id)
    
    # Clean response (remove prefix/suffix if present)
    clean_response = response.replace("🤖 **جمی:** ", "").replace("✨", "").strip()
    
    # Send response
    await event.respond(clean_response, parse_mode="markdown", reply_to=None)
    
    # Update personality tracking
    personality.update_user_interaction(event.sender_id, user_name, message, clean_response)
    
    # Store in vector memory (if available)
    try:
        # Note: This would need actual embedding generation
        # For now, just store in simple memory
        pass
    except Exception:
        pass

# Removed - integrated into handle_ai_social

def register_ai_handlers(client) -> None:
    print("[DEBUG] Registering AI social handlers")
    client.add_event_handler(
        handle_ai_social,
        events.NewMessage(incoming=True)
    )
    print("[DEBUG] AI social handlers registered successfully")