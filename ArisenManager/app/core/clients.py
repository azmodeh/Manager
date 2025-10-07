from telethon import TelegramClient
from telethon.sessions import StringSession
from typing import Optional
from ..utils.config_loader import config_loader
from ..utils.text_loader import text_loader

class BotClients:
    def __init__(self) -> None:
        self.config = config_loader.get_telegram_config()
        self.sudo_id = self.config.get("sudo_id", self.config.get("sudo"))
        self.userbot: Optional[TelegramClient] = None
        self.apibot: Optional[TelegramClient] = None
    
    async def start_userbot(self, session_string: str) -> bool:
        try:
            self.userbot = TelegramClient(
                StringSession(session_string),
                self.config["api_id"],
                self.config["api_hash"]
            )
            await self.userbot.start()
            return True
        except Exception as e:
            print(text_loader.get_error("telegram.auth", error=str(e)))
            return False
    
    async def start_apibot(self, session_string: str) -> bool:
        try:
            self.apibot = TelegramClient(
                StringSession(session_string),
                self.config["api_id"],
                self.config["api_hash"]
            )
            await self.apibot.start(bot_token=self.config["bot_token"])
            return True
        except Exception as e:
            print(text_loader.get_error("telegram.auth", error=str(e)))
            return False
    
    async def notify_sudo_online(self) -> None:
        try:
            if self.userbot:
                userbot_msg = text_loader.get_text("admin.online", bot_type="UserBot")
                await self.userbot.send_message(self.sudo_id, userbot_msg)
            
            if self.apibot:
                apibot_msg = text_loader.get_text("admin.online", bot_type="API Bot")
                await self.apibot.send_message(self.sudo_id, apibot_msg)
        except Exception:
            pass

bot_clients = BotClients()