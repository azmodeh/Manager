from telethon import TelegramClient
from typing import List
from app.repos.sudo_repo import SudoRepository
from app.utils.replies import ReplyHelper
from app.core.config_loader import ConfigLoader
from app.core.logger import MessageLogger

logger = MessageLogger(__name__)


class NotificationService:
    """Service for sending notifications to sudo users."""
    
    def __init__(self) -> None:
        self.sudo_repo = SudoRepository()
        self.reply_helper = ReplyHelper()
        self.config_sudo = ConfigLoader().load_yaml("env.yml")["telegram"]["sudo"]
    
    async def _get_sudo_users(self) -> List[int]:
        """Get all sudo users including config sudo."""
        sudo_users = await self.sudo_repo.get_all_sudos()
        if self.config_sudo not in sudo_users:
            sudo_users.append(self.config_sudo)
        return sudo_users
    
    async def _notify_sudos(self, client: TelegramClient, message_key: str) -> None:
        """Send notification to all sudo users."""
        try:
            sudo_users = await self._get_sudo_users()
            
            for user_id in sudo_users:
                try:
                    await self.reply_helper.send_to_user(client, user_id, message_key)
                except Exception as e:
                    logger.warning("notification_failed", user_id=user_id, error=str(e))
        
        except Exception as e:
            logger.error("notification_service_error", error=str(e))
    
    async def notify_userbot_online(self, client: TelegramClient) -> None:
        """Notify sudo users that userbot is online."""
        await self._notify_sudos(client, "online_ping_body_userbot")
    
    async def notify_bot_online(self, client: TelegramClient) -> None:
        """Notify sudo users that bot API is online."""
        await self._notify_sudos(client, "online_ping_body_botapi")