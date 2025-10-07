import aiosqlite
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from ..utils.config_loader import config_loader
from ..utils.text_loader import text_loader

class Database:
    def __init__(self) -> None:
        self.config = config_loader.get_database_config()
        self.db_path = Path(__file__).parent.parent.parent / "data" / "database.db"
        self.connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> bool:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = await aiosqlite.connect(str(self.db_path))
            await self.create_tables()
            return True
        except Exception as e:
            print(text_loader.get_error("database.connection", error=str(e)))
            return False
    
    async def create_tables(self) -> None:
        if not self.connection:
            return
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                approved INTEGER DEFAULT 0,
                welcome_enabled INTEGER DEFAULT 0,
                welcome_text TEXT,
                welcome_media TEXT,
                welcome_buttons TEXT,
                rules_enabled INTEGER DEFAULT 0,
                rules_text TEXT,
                rules_media TEXT,
                rules_buttons TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.connection.commit()
    
    async def add_group(self, group_id: int, title: str) -> bool:
        if not self.connection:
            return False
        
        try:
            await self.connection.execute(
                "INSERT OR REPLACE INTO groups (id, title) VALUES (?, ?)",
                (group_id, title)
            )
            await self.connection.commit()
            return True
        except Exception:
            return False
    
    async def approve_group(self, group_id: int) -> bool:
        if not self.connection:
            return False
        
        try:
            await self.connection.execute(
                "UPDATE groups SET approved = 1 WHERE id = ?",
                (group_id,)
            )
            await self.connection.commit()
            return True
        except Exception:
            return False
    
    async def get_group_settings(self, group_id: int) -> Optional[Dict[str, Any]]:
        if not self.connection:
            return None
        
        try:
            cursor = await self.connection.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                result = dict(zip(columns, row))
                # Convert JSON strings back to objects
                for key in ['welcome_buttons', 'rules_buttons']:
                    if result.get(key):
                        try:
                            result[key] = json.loads(result[key])
                        except json.JSONDecodeError:
                            result[key] = None
                return result
        except Exception:
            pass
        return None
    
    async def update_group_setting(self, group_id: int, setting: str, value: Any) -> bool:
        if not self.connection:
            return False
        
        try:
            # Convert objects to JSON strings for storage
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            await self.connection.execute(
                f"UPDATE groups SET {setting} = ? WHERE id = ?",
                (value, group_id)
            )
            await self.connection.commit()
            return True
        except Exception:
            return False

database = Database()