from typing import Optional, Any, List, Union
from telethon.events import NewMessage
from telethon.tl.types import KeyboardButton
from app.core.config_loader import ConfigLoader


class ReplyHelper:
    """Helper for sending messages with Persian text."""
    
    def __init__(self) -> None:
        self.messages = ConfigLoader().load_texts("fa")
    
    async def _send_message(self, method, text: str, buttons=None, **kwargs):
        """Internal method to send message."""
        await method(text, buttons=buttons, **kwargs)
    
    async def reply(
        self,
        event: NewMessage.Event,
        message_key: str,
        buttons: Optional[List[List[KeyboardButton]]] = None,
        reply: bool = False,
        **kwargs: Any
    ) -> None:
        """Send message to event chat."""
        text = self.messages.get(message_key, message_key)
        method = event.reply if reply else event.respond
        await self._send_message(method, text, buttons, **kwargs)
    
    async def reply_text(
        self,
        event: NewMessage.Event,
        text: str,
        buttons: Optional[List[List[KeyboardButton]]] = None,
        reply: bool = False,
        **kwargs: Any
    ) -> None:
        """Send custom text to event chat."""
        method = event.reply if reply else event.respond
        await self._send_message(method, text, buttons, **kwargs)
    
    async def send_to_user(
        self,
        client: Any,
        user_id: int,
        message_key: str,
        buttons: Optional[List[List[KeyboardButton]]] = None,
        **kwargs: Any
    ) -> None:
        """Send message to specific user."""
        text = self.messages.get(message_key, message_key)
        await client.send_message(user_id, text, buttons=buttons, **kwargs)
    
    async def send_text_to_user(
        self,
        client: Any,
        user_id: int,
        text: str,
        buttons: Optional[List[List[KeyboardButton]]] = None,
        **kwargs: Any
    ) -> None:
        """Send custom text to specific user."""
        await client.send_message(user_id, text, buttons=buttons, **kwargs)