import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import AuthKeyError, SessionPasswordNeededError, PhoneCodeInvalidError
from typing import Optional
from ..utils.config_loader import config_loader
from ..utils.text_loader import text_loader

logger = logging.getLogger(__name__)

class BotClients:
    def __init__(self) -> None:
        import os
        from dotenv import load_dotenv
        load_dotenv("data/.env")
        
        self.telegram_config = {
            "api_id": int(os.getenv("TELEGRAM_API_ID")),
            "api_hash": os.getenv("TELEGRAM_API_HASH"),
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "sudo": int(os.getenv("TELEGRAM_SUDO"))
        }
        self.sudo_id = self.telegram_config["sudo"]
        self.userbot: Optional[TelegramClient] = None
        self.apibot: Optional[TelegramClient] = None
    

    
    async def start_userbot(self, session_string: str) -> bool:
        try:
            self.userbot = TelegramClient(
                StringSession(session_string),
                self.telegram_config["api_id"],
                self.telegram_config["api_hash"]
            )
            await self.userbot.start()
            return True
        except (AuthKeyError, SessionPasswordNeededError, PhoneCodeInvalidError) as e:
            logger.error(text_loader.get_error("telegram.userbot_start_failed", error=str(e)))
            return False
        except Exception as e:
            logger.error(text_loader.get_error("telegram.auth", error=str(e)))
            return False
    
    async def start_apibot(self, session_string: str) -> bool:
        try:
            self.apibot = TelegramClient(
                StringSession(session_string),
                self.telegram_config["api_id"],
                self.telegram_config["api_hash"]
            )
            await self.apibot.start(bot_token=self.telegram_config["bot_token"])
            return True
        except (AuthKeyError, SessionPasswordNeededError, PhoneCodeInvalidError) as e:
            logger.error(text_loader.get_error("telegram.apibot_start_failed", error=str(e)))
            return False
        except Exception as e:
            logger.error(text_loader.get_error("telegram.auth", error=str(e)))
            return False
    
    async def notify_sudo_online(self) -> None:
        pass  # Disabled to prevent empty message errors

bot_clients = BotClients()