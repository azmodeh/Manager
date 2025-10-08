import time
from typing import Dict, List, Optional
from ..core.database import database

class ConversationMemory:
    def __init__(self) -> None:
        self.conversations: Dict[int, List[Dict]] = {}
        self.max_messages = 10
        self.max_age_hours = 24
    
    async def add_message(self, chat_id: int, user_id: int, message: str, response: str, model_name: str) -> None:
        if chat_id not in self.conversations:
            self.conversations[chat_id] = []
        
        conversation = {
            "user_id": user_id,
            "message": message,
            "response": response,
            "model_name": model_name,
            "timestamp": time.time()
        }
        
        self.conversations[chat_id].append(conversation)
        
        # Keep only recent messages
        self._cleanup_conversation(chat_id)
    
    def _cleanup_conversation(self, chat_id: int) -> None:
        if chat_id not in self.conversations:
            return
        
        current_time = time.time()
        max_age = self.max_age_hours * 3600
        
        # Remove old messages
        self.conversations[chat_id] = [
            msg for msg in self.conversations[chat_id]
            if current_time - msg["timestamp"] < max_age
        ]
        
        # Keep only recent messages
        if len(self.conversations[chat_id]) > self.max_messages:
            self.conversations[chat_id] = self.conversations[chat_id][-self.max_messages:]
    
    def get_context(self, chat_id: int) -> str:
        if chat_id not in self.conversations:
            return ""
        
        self._cleanup_conversation(chat_id)
        
        context_parts = []
        for msg in self.conversations[chat_id][-5:]:  # Last 5 messages
            context_parts.append(f"کاربر: {msg['message']}")
            context_parts.append(f"جمی: {msg['response']}")
        
        return "\n".join(context_parts)

memory = ConversationMemory()