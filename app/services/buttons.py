import json
from typing import List, Optional, Dict, Union
from telethon.tl.types import KeyboardButtonUrl, KeyboardButtonCallback


class ButtonService:
    """Service for handling inline buttons."""
    
    def _create_button(self, button: Dict) -> Optional[Union[KeyboardButtonUrl, KeyboardButtonCallback]]:
        """Create single button from config."""
        if not isinstance(button, dict):
            return None
        
        text = button.get("t", "")
        url = button.get("u")
        callback_data = button.get("d")
        
        if url:
            return KeyboardButtonUrl(text, url)
        elif callback_data:
            return KeyboardButtonCallback(text, callback_data.encode())
        return None
    
    def parse_buttons(self, buttons_json: str) -> Optional[List[List]]:
        """Parse JSON buttons to Telethon buttons."""
        try:
            buttons_data = json.loads(buttons_json)
            if not isinstance(buttons_data, list):
                return None
            
            result = []
            for row in buttons_data:
                if not isinstance(row, list):
                    continue
                
                button_row = [btn for button in row if (btn := self._create_button(button))]
                if button_row:
                    result.append(button_row)
            
            return result or None
            
        except Exception:
            return None
    
    def create_buttons_json(self, buttons: List[List[Dict[str, str]]]) -> str:
        """Create JSON string from button configuration."""
        return json.dumps(buttons, ensure_ascii=False)