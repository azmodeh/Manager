import re
import time
import logging
from typing import Dict, List, Optional, Any
from ..core.database import database
from ..utils.config_loader import config_loader
from ..utils.text_loader import text_loader

logger = logging.getLogger(__name__)

class UserProfileManager:
    def __init__(self) -> None:
        self.pending_confirmations: Dict[int, Dict] = {}
        self.config = config_loader.load_yaml("profile_manager.yml")
    
    async def init_tables(self) -> None:
        if not database.connection:
            return
        
        try:
            await database.connection.execute(self.config["queries"]["create_user_profiles"])
            await database.connection.execute(self.config["queries"]["create_user_relations"])
            await database.connection.commit()
        except Exception as e:
            logger.error(text_loader.get_error("profile.tables.init_error", error=str(e)))
    
    async def db_get_user_profile(self, chat_id: int, user_id: int) -> Optional[Dict]:
        if not database.connection:
            return None
        
        try:
            cursor = await database.connection.execute(
                self.config["queries"]["select_user_profile"],
                (chat_id, user_id)
            )
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                profile = dict(zip(columns, row))
                likes_col = self.config["database"]["tables"]["user_profiles"]["columns"]["likes"]
                if profile.get(likes_col):
                    profile[likes_col] = profile[likes_col].split(self.config["validation"]["likes"]["separator"])
                return profile
        except Exception:
            pass
        return None
    
    async def db_set_user_profile(self, chat_id: int, user_id: int, updates: Dict) -> bool:
        if not database.connection:
            return False
        
        try:
            existing = await self.db_get_user_profile(chat_id, user_id) or {}
            
            likes_col = self.config["database"]["tables"]["user_profiles"]["columns"]["likes"]
            for key, value in updates.items():
                if key == likes_col and isinstance(value, list):
                    existing[key] = self.config["validation"]["likes"]["separator"].join(value)
                else:
                    existing[key] = value
            
            updated_at_col = self.config["database"]["tables"]["user_profiles"]["columns"]["updated_at"]
            existing[updated_at_col] = int(time.time())
            
            cols = self.config["database"]["tables"]["user_profiles"]["columns"]
            await database.connection.execute(
                self.config["queries"]["insert_or_replace_profile"],
                (
                    chat_id, user_id,
                    existing.get(cols["first_name"]),
                    existing.get(cols["lang"]),
                    existing.get(cols["humor_level"]),
                    existing.get(cols["tone"]),
                    existing.get(cols["birthday"]),
                    existing.get(cols["likes"]),
                    existing.get(cols["notes"]),
                    existing.get(cols["updated_at"])
                )
            )
            
            await database.connection.commit()
            return True
        except Exception:
            return False
    
    def parse_language(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for lang_key, lang_config in self.config["parsing"]["languages"].items():
            for keyword in lang_config["keywords"]:
                if keyword in text or keyword in text_lower:
                    return lang_config["code"]
        return None
    
    def parse_tone(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for tone_key, tone_config in self.config["parsing"]["tones"].items():
            for keyword in tone_config["keywords"]:
                if keyword in text or keyword in text_lower:
                    return tone_config["code"]
        return None
    
    def parse_humor(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for humor_key, humor_config in self.config["parsing"]["humor_levels"].items():
            for keyword in humor_config["keywords"]:
                if keyword in text or keyword in text_lower:
                    return humor_config["code"]
        return None
    
    def parse_birthday(self, text: str) -> Optional[str]:
        pattern = self.config["validation"]["birthday"]["pattern"]
        match = re.search(pattern, text)
        if match:
            year, month, day = match.groups()
            try:
                validation = self.config["validation"]["birthday"]
                year_int = int(year)
                month_int = int(month)
                day_int = int(day)
                
                if (validation["year_min"] <= year_int <= validation["year_max"] and
                    validation["month_min"] <= month_int <= validation["month_max"] and
                    validation["day_min"] <= day_int <= validation["day_max"]):
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except ValueError:
                pass
        return None
    
    def parse_likes(self, text: str) -> List[str]:
        split_char = self.config["validation"]["likes"]["split_char"]
        separator = self.config["validation"]["likes"]["separator"]
        min_length = self.config["validation"]["likes"]["min_length"]
        
        if split_char in text:
            likes_part = text.split(split_char, 1)[1]
        else:
            likes_part = text
        
        likes = [like.strip() for like in likes_part.split(separator)]
        return [like for like in likes if like and len(like) > min_length]

profile_manager = UserProfileManager()