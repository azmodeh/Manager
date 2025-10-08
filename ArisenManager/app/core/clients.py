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
        self.telegram_config = config_loader.get_telegram_config()
        self.clients_config = config_loader.load_yaml("clients.yml")
        self.sudo_id = self._get_sudo_id()
        self.userbot: Optional[TelegramClient] = None
        self.apibot: Optional[TelegramClient] = None
    
    def _get_sudo_id(self) -> int:
        """Get sudo ID from config with fallback"""
        config_keys = self.clients_config["config_keys"]
        return self.telegram_config.get(
            config_keys["sudo_id"], 
            self.telegram_config.get(config_keys["sudo_fallback"])
        )
    
    async def start_userbot(self, session_string: str) -> bool:
        try:
            config_keys = self.clients_config["config_keys"]
            self.userbot = TelegramClient(
                StringSession(session_string),
                self.telegram_config[config_keys["api_id"]],
                self.telegram_config[config_keys["api_hash"]]
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
            config_keys = self.clients_config["config_keys"]
            self.apibot = TelegramClient(
                StringSession(session_string),
                self.telegram_config[config_keys["api_id"]],
                self.telegram_config[config_keys["api_hash"]]
            )
            await self.apibot.start(bot_token=self.telegram_config[config_keys["bot_token"]])
            return True
        except (AuthKeyError, SessionPasswordNeededError, PhoneCodeInvalidError) as e:
            logger.error(text_loader.get_error("telegram.apibot_start_failed", error=str(e)))
            return False
        except Exception as e:
            logger.error(text_loader.get_error("telegram.auth", error=str(e)))
            return False
    
    async def notify_sudo_online(self) -> None:
        try:
            bot_types = self.clients_config["bot_types"]
            
            if self.userbot:
                userbot_msg = text_loader.get_text("admin.online", bot_type=bot_types["userbot"])
                await self.userbot.send_message(self.sudo_id, userbot_msg)
            
            if self.apibot:
                apibot_msg = text_loader.get_text("admin.online", bot_type=bot_types["apibot"])
                await self.apibot.send_message(self.sudo_id, apibot_msg)
        except Exception as e:
            logger.warning(text_loader.get_error("telegram.notification_failed", error=str(e)))

bot_clients = BotClients()