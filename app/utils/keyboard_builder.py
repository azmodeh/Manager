from typing import List, Optional
from telethon.tl.types import KeyboardButtonCallback
from app.core.config_loader import ConfigLoader


class KeyboardBuilder:
    """Build keyboards from YAML configuration."""
    
    def __init__(self):
        config_loader = ConfigLoader()
        self.keyboards = config_loader.load_yaml("data/config/keyboards.yml")
        self.callbacks = config_loader.load_yaml("data/config/callback_config.yml")
        self.prefix = self.callbacks["callback_patterns"]["prefix"]
        self.separator = self.callbacks["callback_patterns"]["separator"]
    
    def _build_buttons(self, buttons_config: List, chat_id: int, status: Optional[str] = None) -> List[List[KeyboardButtonCallback]]:
        """Build keyboard buttons from config."""
        return [
            [
                KeyboardButtonCallback(
                    btn["text"].format(status=status) if "{status}" in btn["text"] and status else btn["text"],
                    self._build_callback_data(btn["callback_data"], chat_id).encode()
                )
                for btn in row["buttons"]
            ]
            for row in buttons_config
        ]
    
    def build_admin_panel(self, chat_id: int) -> List[List[KeyboardButtonCallback]]:
        """Build main admin panel keyboard."""
        return self._build_buttons(self.keyboards["admin_panel"]["main_buttons"], chat_id)
    
    def build_feature_menu(self, feature: str, chat_id: int, status: Optional[str] = None) -> List[List[KeyboardButtonCallback]]:
        """Build feature menu keyboard."""
        if feature not in self.keyboards["feature_menus"]:
            return []
        return self._build_buttons(self.keyboards["feature_menus"][feature]["buttons"], chat_id, status)
    
    def get_feature_title(self, feature: str) -> str:
        """Get feature menu title."""
        return self.keyboards["feature_menus"].get(feature, {}).get("title", "")
    
    def get_status_label(self, enabled: bool) -> str:
        """Get status label."""
        return self.keyboards["status_labels"]["enabled" if enabled else "disabled"]
    
    def get_common_button(self, button_type: str) -> str:
        """Get common button text."""
        return self.keyboards["common_buttons"].get(button_type, "")
    
    def _build_callback_data(self, callback_pattern: str, chat_id: int) -> str:
        """Build callback data string."""
        parts = callback_pattern.split("|")
        if len(parts) == 2:
            feature, action = parts
            return f"{self.prefix}{self.separator}{feature}{self.separator}{action}{self.separator}{chat_id}"
        return callback_pattern