from telethon import TelegramClient
from telethon.sessions import StringSession
from typing import Optional
import asyncio
from ..utils.config_loader import config_loader
from ..utils.text_loader import text_loader

class SessionGenerator:
    def __init__(self) -> None:
        self.config = config_loader.get_telegram_config()
    
    async def generate_userbot_session(self) -> Optional[str]:
        try:
            client = TelegramClient(
                StringSession(),
                self.config["api_id"],
                self.config["api_hash"]
            )
            
            await client.start(phone=self.config["phone_number"])
            session_string = client.session.save()
            await client.disconnect()
            
            return session_string
        except Exception as e:
            print(text_loader.get_error("telegram.session", error=str(e)))
            return None
    
    async def generate_bot_session(self) -> Optional[str]:
        try:
            client = TelegramClient(
                StringSession(),
                self.config["api_id"],
                self.config["api_hash"]
            )
            
            await client.start(bot_token=self.config["bot_token"])
            session_string = client.session.save()
            await client.disconnect()
            
            return session_string
        except Exception as e:
            print(text_loader.get_error("telegram.session", error=str(e)))
            return None

session_generator = SessionGenerator()