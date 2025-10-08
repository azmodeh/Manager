import random
import time
import logging
from typing import Dict, List, Optional
from ..utils.config_loader import config_loader
from ..utils.text_loader import text_loader

logger = logging.getLogger(__name__)

class AIPersonality:
    def __init__(self) -> None:
        self.config = config_loader.load_config("ai.yml")
        self.personality_config = config_loader.load_yaml("personality.yml")
        self.user_interactions: Dict[int, Dict] = {}
        self.rate_limits: Dict[int, List[float]] = {}
    
    def get_user_name(self, user) -> str:
        """Extract user's display name"""
        if hasattr(user, 'first_name') and user.first_name:
            return user.first_name
        elif hasattr(user, 'username') and user.username:
            return user.username
        return text_loader.get_text("ui.default_user_name")
    
    def should_respond(self, message: str, user_id: int, is_reply: bool = False, is_mention: bool = False) -> bool:
        """Determine if AI should respond based on context"""
        if not self._check_rate_limit(user_id):
            return False
        
        if is_mention or is_reply:
            return True
        
        message_lower = message.lower()
        for keyword in self.config["triggers"]["mention_keywords"]:
            if keyword in message_lower:
                return True
        
        for ending in self.config["triggers"]["question_endings"]:
            if message.endswith(ending):
                return True
        
        return False
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limits"""
        current_time = time.time()
        window = self.config["policy"]["rate_limit_window_sec"]
        limit = self.config["policy"]["rate_limit_per_user"]
        
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        cutoff = current_time - window
        self.rate_limits[user_id] = [
            t for t in self.rate_limits[user_id] if t > cutoff
        ]
        
        if len(self.rate_limits[user_id]) >= limit:
            return False
        
        self.rate_limits[user_id].append(current_time)
        return True
    
    def build_context_prompt(self, message: str, user_name: str, chat_context: List[str]) -> str:
        """Build context-aware prompt for AI"""
        max_length = self.config["personality"]["max_reply_length"]
        prompts = self.personality_config["prompts"]
        formatting = self.personality_config["formatting"]
        
        base_prompt = (
            prompts["base_intro"] + formatting["newline"] +
            prompts["personality_desc"] + formatting["newline"] +
            prompts["language_desc"] + formatting["newline"] +
            prompts["user_name_prefix"].format(user_name=user_name) + formatting["double_newline"]
        )
        
        rules_lines = [formatting["rule_prefix"] + rule.format(max_length=max_length) for rule in prompts["rules"]]
        rules_prompt = (
            prompts["rules_header"] + formatting["newline"] +
            formatting["newline"].join(rules_lines) + formatting["double_newline"]
        )
        
        personality_prompt = base_prompt + rules_prompt
        
        if chat_context:
            context_limit = formatting["context_limit"]
            recent_context = formatting["newline"].join(chat_context[-context_limit:])
            personality_prompt += (
                prompts["context_header"] + formatting["newline"] +
                recent_context + formatting["double_newline"]
            )
        
        personality_prompt += (
            prompts["message_prefix"].format(user_name=user_name, message=message) +
            formatting["double_newline"] + prompts["response_prefix"]
        )
        
        return personality_prompt
    
    def get_random_greeting(self, user_name: str) -> str:
        """Get random greeting for user"""
        greetings = self.config["personality"]["greeting_variants"]
        greeting = random.choice(greetings)
        return greeting.format(name=user_name)
    
    def update_user_interaction(self, user_id: int, user_name: str, message: str, response: str) -> None:
        """Track user interaction patterns"""
        if user_id not in self.user_interactions:
            default_fields = self.personality_config["user_interaction"]["default_fields"]
            self.user_interactions[user_id] = default_fields.copy()
        
        interaction = self.user_interactions[user_id]
        interaction["message_count"] += 1
        interaction["last_interaction"] = time.time()
        interaction["name"] = user_name
        
        mood_config = self.personality_config["mood_detection"]
        happy_indicators = mood_config["happy_indicators"]
        sad_indicators = mood_config["sad_indicators"]
        
        if any(word in message.lower() for word in happy_indicators):
            interaction["mood"] = mood_config["happy_mood"]
        elif any(word in message.lower() for word in sad_indicators):
            interaction["mood"] = mood_config["sad_mood"]
        else:
            interaction["mood"] = mood_config["neutral_mood"]

personality = AIPersonality()