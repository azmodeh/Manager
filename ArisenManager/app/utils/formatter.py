import logging
import re
from typing import Any, Optional, Dict
from telegramify_markdown import markdownify
import emoji
from .text_loader import text_loader
from .config_loader import config_loader

logger = logging.getLogger(__name__)

class MessageFormatter:
    def __init__(self) -> None:
        self.config = config_loader.load_yaml("formatter.yml")
    
    def _validate_input(self, text: str, **kwargs: Any) -> bool:
        """Validate input for security"""
        try:
            security_config = self.config["security"]
            
            # Check text length
            max_length = security_config["max_format_length"]
            if len(text) > max_length:
                logger.warning(text_loader.get_error("formatter.text_too_long", 
                                                   length=len(text), 
                                                   max_length=max_length))
                return False
            
            # Check kwargs count
            max_kwargs = security_config["max_kwargs_count"]
            if len(kwargs) > max_kwargs:
                logger.warning(text_loader.get_error("formatter.too_many_kwargs", 
                                                   count=len(kwargs), 
                                                   max_count=max_kwargs))
                return False
            
            # Check for forbidden patterns
            forbidden_patterns = security_config["forbidden_patterns"]
            text_lower = text.lower()
            for pattern in forbidden_patterns:
                if pattern in text_lower:
                    logger.warning(text_loader.get_error("formatter.forbidden_pattern", pattern=pattern))
                    return False
            
            return True
        except Exception as e:
            logger.error(text_loader.get_error("formatter.format_error", error=str(e)))
            return False
    
    def _sanitize_kwargs(self, **kwargs: Any) -> Dict[str, Any]:
        """Sanitize format arguments"""
        sanitized = {}
        allowed_chars = self.config["placeholders"]["allowed_chars"]
        max_length = self.config["placeholders"]["max_length"]
        
        for key, value in kwargs.items():
            # Sanitize key
            clean_key = ''.join(c for c in str(key) if c in allowed_chars)[:max_length]
            
            # Sanitize value
            if isinstance(value, str):
                # Remove potentially dangerous characters
                clean_value = re.sub(r'[<>"\']', '', str(value))[:max_length]
            else:
                clean_value = str(value)[:max_length]
            
            sanitized[clean_key] = clean_value
        
        return sanitized
    
    def format_markdown(self, text: str) -> str:
        """Format text as markdown"""
        try:
            return markdownify(text)
        except Exception as e:
            logger.error(text_loader.get_error("formatter.markdown_error", error=str(e)))
            return text
    
    def add_emojis(self, text: str, emoji_map: Optional[dict] = None) -> str:
        """Add emojis to text"""
        try:
            if emoji_map:
                for key, emoji_key in emoji_map.items():
                    emoji_char = text_loader.get_emoji(emoji_key)
                    text = text.replace(f"{{{key}}}", emoji_char)
            
            emoji_config = self.config["emoji"]
            if emoji_config["enable_conversion"]:
                return emoji.emojize(text)
            return text
        except Exception as e:
            logger.error(text_loader.get_error("formatter.emoji_conversion_error", error=str(e)))
            return text
    
    def format_user_mention(self, user_id: int, first_name: str) -> str:
        """Format user mention link"""
        try:
            template = self.config["url_templates"]["user_mention"]
            sanitized_name = re.sub(r'[<>"\']', '', first_name)[:50]
            return f"[{sanitized_name}]({template.format(user_id=user_id)})"
        except Exception as e:
            logger.error(text_loader.get_error("formatter.format_error", error=str(e)))
            return first_name
    
    def format_message(self, text: str, format_type: str = None, **kwargs: Any) -> str:
        """Format message with security validation"""
        try:
            # Set default format type
            if format_type is None:
                format_type = self.config["format_types"]["markdown"]
            
            # Validate input
            if not self._validate_input(text, **kwargs):
                return text
            
            # Sanitize arguments
            safe_kwargs = self._sanitize_kwargs(**kwargs)
            
            # Format text safely
            try:
                formatted_text = text.format(**safe_kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(text_loader.get_error("formatter.format_error", error=str(e)))
                formatted_text = text
            
            # Apply format type
            format_types = self.config["format_types"]
            if format_type == format_types["markdown"]:
                formatted_text = self.format_markdown(formatted_text)
            elif format_type not in format_types.values():
                logger.warning(text_loader.get_error("formatter.invalid_format_type", format_type=format_type))
            
            # Add emojis
            formatted_text = self.add_emojis(formatted_text)
            
            return formatted_text
            
        except Exception as e:
            logger.error(text_loader.get_error("formatter.format_error", error=str(e)))
            return text

message_formatter = MessageFormatter()