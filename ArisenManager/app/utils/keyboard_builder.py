from typing import List, Dict, Any, Optional
from keyboa.keyboards import keyboa_maker
from .config_loader import config_loader

class KeyboardBuilder:
    def __init__(self) -> None:
        pass
    
    def build_from_template(self, template_name: str, **kwargs: Any) -> List[List[Dict[str, str]]]:
        template = config_loader.get_keyboard_template(template_name)
        if not template:
            return []
        
        keyboard = []
        for row in template:
            if isinstance(row, dict):
                button = {
                    "text": row["text"].format(**kwargs),
                    "callback_data": row["callback"]
                }
                keyboard.append([button])
            elif isinstance(row, list):
                button_row = []
                for btn in row:
                    button = {
                        "text": btn["text"].format(**kwargs),
                        "callback_data": btn["callback"]
                    }
                    button_row.append(button)
                keyboard.append(button_row)
        
        return keyboard
    
    def build_inline_keyboard(self, buttons: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
        return keyboa_maker(buttons, items_per_row=2)
    
    def build_reply_keyboard(self, buttons: List[str]) -> List[List[str]]:
        return keyboa_maker(buttons, items_per_row=2)

keyboard_builder = KeyboardBuilder()