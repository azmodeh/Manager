from typing import Any, Optional
from telegramify_markdown import markdownify
import emoji
from .text_loader import text_loader

class MessageFormatter:
    def __init__(self) -> None:
        pass
    
    def format_markdown(self, text: str) -> str:
        return markdownify(text)
    
    def add_emojis(self, text: str, emoji_map: Optional[dict] = None) -> str:
        if emoji_map:
            for key, emoji_key in emoji_map.items():
                emoji_char = text_loader.get_emoji(emoji_key)
                text = text.replace(f"{{{key}}}", emoji_char)
        return emoji.emojize(text)
    
    def format_user_mention(self, user_id: int, first_name: str) -> str:
        return f"[{first_name}](tg://user?id={user_id})"
    
    def format_message(self, text: str, format_type: str = "markdown", **kwargs: Any) -> str:
        formatted_text = text.format(**kwargs)
        
        if format_type == "markdown":
            formatted_text = self.format_markdown(formatted_text)
        
        formatted_text = self.add_emojis(formatted_text)
        return formatted_text

message_formatter = MessageFormatter()