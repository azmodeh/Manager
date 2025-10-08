from telethon import TelegramClient
from telethon.sessions import StringSession
from typing import Optional
import asyncio
import logging
from ..utils.config_loader import config_loader
from ..utils.text_loader import text_loader

logger = logging.getLogger(__name__)

class SessionGenerator:
    def __init__(self) -> None:
        import os
        from dotenv import load_dotenv
        load_dotenv("data/.env")
        
        self.config = {
            "api_id": int(os.getenv("TELEGRAM_API_ID")),
            "api_hash": os.getenv("TELEGRAM_API_HASH"),
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "phone_number": os.getenv("TELEGRAM_PHONE_NUMBER")
        }
    
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
            logger.error(text_loader.get_error("telegram.session", error=str(e)))
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
            logger.error(text_loader.get_error("telegram.session", error=str(e)))
            return None

session_generator = SessionGenerator()