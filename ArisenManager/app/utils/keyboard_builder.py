import logging
from typing import List, Dict, Any, Optional
from keyboa.keyboards import keyboa_maker
from .config_loader import config_loader
from .text_loader import text_loader

logger = logging.getLogger(__name__)

class KeyboardBuilder:
    def __init__(self) -> None:
        self.config = config_loader.load_yaml("keyboard_builder.yml")
    
    def build_from_template(self, template_name: str, **kwargs: Any) -> List[List[Dict[str, str]]]:
        try:
            template = config_loader.get_keyboard_template(template_name)
            if not template:
                logger.warning(text_loader.get_error("keyboard.template_not_found", template=template_name))
                return []
            
            keyboard = []
            text_key = self.config["button_keys"]["text"]
            callback_key = self.config["button_keys"]["callback"]
            callback_data_key = self.config["button_keys"]["callback_data"]
            
            for row in template:
                if isinstance(row, dict):
                    try:
                        button = {
                            text_key: row[text_key].format(**kwargs),
                            callback_data_key: row[callback_key]
                        }
                        keyboard.append([button])
                    except (KeyError, ValueError) as e:
                        logger.error(text_loader.get_error("keyboard.format_error", error=str(e)))
                        continue
                elif isinstance(row, list):
                    button_row = []
                    for btn in row:
                        try:
                            button = {
                                text_key: btn[text_key].format(**kwargs),
                                callback_data_key: btn[callback_key]
                            }
                            button_row.append(button)
                        except (KeyError, ValueError) as e:
                            logger.error(text_loader.get_error("keyboard.format_error", error=str(e)))
                            continue
                    if button_row:
                        keyboard.append(button_row)
            
            return keyboard
        except Exception as e:
            logger.error(text_loader.get_error("keyboard.build_error", error=str(e)))
            return []
    
    def build_inline_keyboard(self, buttons: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
        try:
            items_per_row = self.config["settings"]["default_items_per_row"]
            return keyboa_maker(buttons, items_per_row=items_per_row)
        except Exception as e:
            logger.error(text_loader.get_error("keyboard.build_error", error=str(e)))
            return []
    
    def build_reply_keyboard(self, buttons: List[str]) -> List[List[str]]:
        try:
            items_per_row = self.config["settings"]["default_items_per_row"]
            return keyboa_maker(buttons, items_per_row=items_per_row)
        except Exception as e:
            logger.error(text_loader.get_error("keyboard.build_error", error=str(e)))
            return []

keyboard_builder = KeyboardBuilder()