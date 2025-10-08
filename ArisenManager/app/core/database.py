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
        self.config = config_loader.get_database_config()
        self.db_config = config_loader.load_yaml("database.yml")
        self.db_path = self._get_db_path()
        self.connection: Optional[aiosqlite.Connection] = None
    
    def _get_db_path(self) -> Path:
        """Get database file path from configuration"""
        base_path = Path(__file__).parent.parent.parent
        db_dir = self.db_config["paths"]["db_dir"]
        db_file = self.db_config["paths"]["db_file"]
        return base_path / db_dir / db_file
    
    async def connect(self) -> bool:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = await aiosqlite.connect(str(self.db_path))
            await self.create_tables()
            return True
        except Exception as e:
            logger.error(text_loader.get_error("database.connection", error=str(e)))
            return False
    
    async def create_tables(self) -> None:
        if not self.connection:
            return
        
        try:
            queries = self.db_config["queries"]
            await self.connection.execute(queries["create_groups_table"])
            await self.connection.execute(queries["create_settings_table"])
            await self.connection.commit()
            
            await self._add_missing_columns()
        except Exception as e:
            logger.error(text_loader.get_error("database.table_creation", error=str(e)))
    
    async def _add_missing_columns(self) -> None:
        """Add missing columns if they don't exist"""
        try:
            queries = self.db_config["queries"]
            column_queries = [
                queries["add_start_enabled_column"],
                queries["add_start_text_column"],
                queries["add_help_enabled_column"],
                queries["add_help_text_column"]
            ]
            
            for query in column_queries:
                try:
                    await self.connection.execute(query)
                except Exception:
                    pass  # Column already exists
            
            await self.connection.commit()
        except Exception as e:
            logger.warning(text_loader.get_error("database.column_add", error=str(e)))
    
    async def add_group(self, group_id: int, title: str) -> bool:
        if not self.connection:
            return False
        
        try:
            query = self.db_config["queries"]["insert_or_replace_group"]
            await self.connection.execute(query, (group_id, title))
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
        
        try:
            # Convert objects to JSON strings for storage
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            query_template = self.db_config["queries"]["update_group_setting"]
            query = query_template.format(setting=setting)
            await self.connection.execute(query, (value, group_id))
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(text_loader.get_error("database.group_update", error=str(e)))
            return False

database = Database()