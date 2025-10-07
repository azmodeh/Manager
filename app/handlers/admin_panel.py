from telethon.events import NewMessage, CallbackQuery
from app.utils.auth import AuthFilter
from app.utils.replies import ReplyHelper
from app.utils.keyboard_builder import KeyboardBuilder
from app.repos.group_repo import GroupRepository
from app.core.logger import MessageLogger
from app.core.config_loader import ConfigLoader

logger = MessageLogger(__name__)
auth = AuthFilter()
reply_helper = ReplyHelper()
group_repo = GroupRepository()
keyboard_builder = KeyboardBuilder()
config_loader = ConfigLoader()


class AdminPanelHandler:
    """Handler for group admin panel."""
    
    def __init__(self) -> None:
        self._messages = config_loader.load_texts("fa")
        self._config = config_loader.load_yaml("env.yml")["app"]
    
    async def handle_panel(self, event: NewMessage.Event) -> None:
        """Handle /panel command.
        
        Args:
            event: Telethon event
        """
        if not await auth.is_group(event):
            return

        if not await auth.is_sudo(event.sender_id):
            if not await auth.is_group_admin(event):
                await reply_helper.reply(event, "missing_permission")
                return
        
        await reply_helper.reply(event, "panel_title", buttons=keyboard_builder.build_admin_panel(event.chat_id))  # type: ignore
    
    async def handle_callback(self, event: CallbackQuery.Event) -> None:
        """Handle callback queries from admin panel."""
        try:
            
            data = event.data.decode()
            separator = self._config.get("callback_separator", "|")
            parts = data.split(separator)
            
            if len(parts) < 4 or parts[0] != self._config.get("cfg_prefix", "CFG"):
                return
            
            feature, action, chat_id = parts[1], parts[2], int(parts[3])
            
            if not event.sender_id or not await auth.is_sudo(event.sender_id):
                await event.answer(self._messages.get("missing_permission", ""))
                return
            
            back_action = self._config.get("back_action", "BACK")
            
            if action == self._config.get("menu_action", "MENU"):
                await self.show_feature_menu(event, feature, chat_id)
            elif action == self._config.get("toggle_action", "TOGGLE"):
                await self.toggle_feature(event, feature, chat_id)
            elif action == back_action:
                await self.show_main_panel(event, chat_id)
                
        except Exception as e:
            logger.error("callback_error", error=str(e))
            await event.answer(self._messages.get("callback_error", ""))
    
    async def show_feature_menu(self, event: CallbackQuery.Event, feature: str, chat_id: int) -> None:
        """Show feature configuration menu."""
        
        feature_config = await group_repo.get_group_feature(chat_id, feature)
        await event.edit(
            keyboard_builder.get_feature_title(feature),
            buttons=keyboard_builder.build_feature_menu(
                feature,
                chat_id,
                keyboard_builder.get_status_label(bool(feature_config.enabled) if feature_config else False)
            )
        )
    
    async def toggle_feature(self, event: CallbackQuery.Event, feature: str, chat_id: int) -> None:
        """Toggle feature on/off."""
        
        config = await group_repo.get_group_feature(chat_id, feature)
        new_status = not (bool(config.enabled) if config else False)
        
        await group_repo.upsert_group_feature(
            chat_id=chat_id,
            feature=feature,
            enabled=new_status,
            updated_by=event.sender_id
        )
        
        status_key = "status_enabled" if new_status else "status_disabled"
        await event.answer(self._messages.get(status_key, ""))
        await self.show_feature_menu(event, feature, chat_id)
    
    async def show_main_panel(self, event: CallbackQuery.Event, chat_id: int) -> None:
        """Show main admin panel."""
        await event.edit(
            text=self._messages.get("panel_title", ""),
            buttons=keyboard_builder.build_admin_panel(chat_id)
        )  # type: ignore


def register_handlers(userbot, bot) -> None:
    """Register admin panel handlers."""
    handler = AdminPanelHandler()
    
    bot.add_event_handler(
        handler.handle_panel,
        NewMessage(pattern=f"^{handler._config.get('panel_command', '/panel')}$")
    )
    
    bot.add_event_handler(
        handler.handle_callback,
        CallbackQuery(pattern=handler._config.get("cfg_prefix", "CFG").encode())
    )
    
    logger.info("handler_registered")