import aiosqlite
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from ..utils.config_loader import config_loader
from ..utils.text_loader import text_loader

logger = logging.getLogger(__name__)

class Database:
    def __init__(self) -> None:
        self.db_path = Path(__file__).parent.parent.parent / "data" / "database.db"
        self.connection: Optional[aiosqlite.Connection] = None
    

    
    async def connect(self) -> bool:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = await aiosqlite.connect(str(self.db_path))
            await self.create_tables()
            return True
        except OSError as e:
            logger.error(text_loader.get_error("database.path_error", error=str(e)))
            return False
        except aiosqlite.Error as e:
            logger.error(text_loader.get_error("database.connection", error=str(e)))
            return False
    
    async def create_tables(self) -> None:
        if not self.connection:
            return
        
        try:
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    approved INTEGER DEFAULT 0
                )
            """)
            await self.connection.commit()
        except aiosqlite.Error as e:
            logger.error(text_loader.get_error("database.table_creation", error=str(e)))
    

    
    async def add_group(self, group_id: int, title: str) -> bool:
        if not self.connection:
            return False
        
        try:
            await self.connection.execute(
                "INSERT OR REPLACE INTO groups (id, name) VALUES (?, ?)",
                (group_id, title)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(text_loader.get_error("database.group_add", error=str(e)))
            return False
    
    async def approve_group(self, group_id: int) -> bool:
        if not self.connection:
            return False
        
        try:
            query = self.db_config["queries"]["update_group_approved"]
            await self.connection.execute(query, (group_id,))
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(text_loader.get_error("database.group_approve", error=str(e)))
            return False
    
    async def reject_group(self, group_id: int) -> bool:
        """Reject a group by removing it from database"""
        if not self.connection:
            return False
        
        try:
            await self.connection.execute("DELETE FROM groups WHERE id = ?", (group_id,))
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(text_loader.get_error("database.group_update", error=str(e)))
            return False
    
    async def get_group_settings(self, group_id: int) -> Optional[Dict[str, Any]]:
        if not self.connection:
            return None
        
        try:
            query = self.db_config["queries"]["select_group_by_id"]
            cursor = await self.connection.execute(query, (group_id,))
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                result = dict(zip(columns, row))
                
                # Convert JSON strings back to objects
                json_columns = self.db_config["json_columns"]
                for key in json_columns:
                    if result.get(key):
                        try:
                            result[key] = json.loads(result[key])
                        except json.JSONDecodeError as e:
                            logger.warning(text_loader.get_error("database.json_parse", column=key, error=str(e)))
                            result[key] = None
                return result
        except Exception as e:
            logger.error(text_loader.get_error("database.group_settings", error=str(e)))
        return None
    
    async def update_group_setting(self, group_id: int, setting: str, value: Any) -> bool:
        if not self.connection:
            return False
        
        # Whitelist of allowed column names to prevent SQL injection
        allowed_settings = {
            "name", "approved", "start_enabled", "start_text", 
            "help_enabled", "help_text", "ai_enabled", "ai_personality",
            "ai_model", "ai_temperature", "ai_max_tokens"
        }
        
        if setting not in allowed_settings:
            logger.error(text_loader.get_error("database.invalid_setting", setting=setting))
            return False
        
        try:
            # Convert objects to JSON strings for storage
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            # Safe query construction with validated column name
            query = f"UPDATE groups SET {setting} = ? WHERE id = ?"
            await self.connection.execute(query, (value, group_id))
            await self.connection.commit()
            return True
        except aiosqlite.Error as e:
            logger.error(text_loader.get_error("database.group_update", error=str(e)))
            return False

database = Database()