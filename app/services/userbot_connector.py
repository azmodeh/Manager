from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest, ExportChatInviteRequest
from app.core.config_loader import ConfigLoader
from app.core.logger import MessageLogger

logger = MessageLogger(__name__)


class UserbotConnector:
    """Service for connecting userbot to approved groups."""
    
    def __init__(self) -> None:
        self.join_prefix = ConfigLoader().load_yaml("env.yml")["app"].get("join_command_prefix", "JOIN_GROUP:")
    
    async def join_group_by_link(self, userbot: TelegramClient, invite_link: str) -> bool:
        """Join group using invite link."""
        try:
            if 'joinchat/' in invite_link or '+' in invite_link:
                hash_part = invite_link.split('/')[-1].replace('+', '')
            else:
                hash_part = invite_link
            
            await userbot(ImportChatInviteRequest(hash_part))
            logger.info("userbot_joined_group")
            return True
        except Exception as e:
            logger.error("userbot_join_failed", error=str(e))
            return False
    
    async def send_join_request(self, bot_client: TelegramClient, userbot: TelegramClient, chat_id: int) -> None:
        """Send join request to userbot via private message."""
        try:
            result = await bot_client(ExportChatInviteRequest(chat_id))  # type: ignore
            invite_link = result.link  # type: ignore
            
            me = await userbot.get_me()
            userbot_id = me.id  # type: ignore
            
            message = f"{self.join_prefix}{invite_link}|{chat_id}"
            await bot_client.send_message(userbot_id, message)
            
        except Exception as e:
            logger.error("join_request_failed", error=str(e))
    
    async def promote_to_admin(self, bot_client: TelegramClient, chat_id: int, user_id: int) -> bool:
        """Promote user to admin."""
        try:
            await bot_client.edit_admin(
                chat_id, user_id,
                change_info=True, post_messages=True, edit_messages=True,
                delete_messages=True, ban_users=True, invite_users=True,
                pin_messages=True, add_admins=False, manage_call=True
            )
            logger.info("userbot_promoted")
            return True
        except Exception as e:
            logger.error("promotion_failed", error=str(e))
            return False