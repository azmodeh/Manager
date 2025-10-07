from typing import List, Dict, Any
from telethon.tl.types import KeyboardButtonCallback
from app.core.config_loader import ConfigLoader


class KeyboardBuilder:
    """Build keyboards from configuration."""
    
    def __init__(self):
        config = ConfigLoader().load_yaml("keyboards.yml")
        self.keyboards_config = config
        self.prefix = config["callback_config"]["prefix"]
        self.separator = config["callback_config"]["separator"]
    
    def _create_button(self, text: str, callback_data: str) -> KeyboardButtonCallback:
        """Create keyboard button."""
        return KeyboardButtonCallback(text, callback_data.encode())
    
    def build_admin_main_buttons(self, messages: Dict[str, Any], chat_id: int) -> List[List[KeyboardButtonCallback]]:
        """Build main admin panel buttons."""
        buttons_config = self.keyboards_config["admin_panel"]["main"]
        return [[
            self._create_button(
                messages.get(btn["text_key"], ""),
                self._build_callback_data(btn["callback_data"], chat_id)
            ) for btn in buttons_config
        ]]
    
    def build_feature_menu_buttons(self, messages: Dict[str, Any], feature: str, chat_id: int, status: str) -> List[List[KeyboardButtonCallback]]:
        """Build feature menu buttons."""
        buttons_config = self.keyboards_config["admin_panel"]["feature_menu"]
        buttons = []
        current_row = []
        
        for btn in buttons_config:
            text = messages.get(btn["text_key"], "")
            if btn.get("dynamic_text") and btn["text_key"] == "status_label":
                text = f"{text}: {status}"
            
            callback_data = self._build_callback_data(
                btn["callback_data"].format(feature=feature), chat_id
            )
            
            button = self._create_button(text, callback_data)
            
            if btn["text_key"] in ["edit_text_button", "edit_buttons_button"]:
                current_row.append(button)
                if len(current_row) == 2:
                    buttons.append(current_row)
                    current_row = []
            else:
                if current_row:
                    buttons.append(current_row)
                    current_row = []
                buttons.append([button])
        
        if current_row:
            buttons.append(current_row)
        
        return buttons
    
    def build_approval_buttons(self, messages: Dict[str, Any], chat_id: int) -> List[List[KeyboardButtonCallback]]:
        """Build approval buttons."""
        buttons_config = self.keyboards_config["approval"]["buttons"]
        return [[
            self._create_button(
                messages.get(btn["text_key"], ""),
                f"{btn['callback_data']}|{chat_id}"
            ) for btn in buttons_config
        ]]
    
    def _build_callback_data(self, data: str, chat_id: int) -> str:
        """Build callback data with prefix and chat_id."""
        return f"{self.prefix}{self.separator}{data}{self.separator}{chat_id}"
    
    def parse_callback_data(self, data: str) -> Dict[str, Any]:
        """Parse callback data."""
        parts = data.split(self.separator)
        
        if len(parts) < 4 or parts[0] != self.prefix:
            return {}
        
        return {
            "feature": parts[1],
            "action": parts[2],
            "chat_id": int(parts[3])
        }