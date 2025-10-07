from typing import Optional
from telethon.events import NewMessage
from telethon.tl.types import User, Chat, Channel
from app.core.config_loader import ConfigLoader
from app.repos.sudo_repo import SudoRepository


class AuthFilter:
    """Authentication and authorization filters."""
    
    def __init__(self) -> None:
        self.config_sudo = ConfigLoader().load_yaml("env.yml")["telegram"]["sudo"]
        self.sudo_repo = SudoRepository()
    
    async def is_sudo(self, user_id: int) -> bool:
        """Check if user is sudo admin."""
        return user_id == self.config_sudo or await self.sudo_repo.is_sudo(user_id)
    
    async def is_private(self, event: NewMessage.Event) -> bool:
        """Check if message is from private chat."""
        return isinstance(event.chat, User)
    
    async def is_group(self, event: NewMessage.Event) -> bool:
        """Check if message is from group chat."""
        return isinstance(event.chat, (Chat, Channel))
    
    async def is_group_admin(self, event: NewMessage.Event, user_id: Optional[int] = None) -> bool:
        """Check if user is group administrator."""
        if not await self.is_group(event) or not event.client:
            return False
        
        check_user_id = user_id or event.sender_id
        if not check_user_id:
            return False
        
        try:
            participant = await event.client.get_permissions(event.chat_id, check_user_id)
            return participant.is_admin or participant.is_creator
        except Exception:
            return False
    
    def _create_decorator(self, check_func):
        """Create decorator with check function."""
        def decorator(func):
            async def wrapper(event: NewMessage.Event):
                if await check_func(event):
                    return await func(event)
            return wrapper
        return decorator
    
    def sudo_only(self, func):
        """Decorator for sudo-only handlers."""
        return self._create_decorator(lambda e: self.is_sudo(e.sender_id))(func)
    
    def private_only(self, func):
        """Decorator for private chat only handlers."""
        return self._create_decorator(self.is_private)(func)
    
    def group_only(self, func):
        """Decorator for group chat only handlers."""
        return self._create_decorator(self.is_group)(func)
    
    def admin_or_sudo(self, func):
        """Decorator for group admin or sudo handlers."""
        async def check(event):
            return await self.is_sudo(event.sender_id) or await self.is_group_admin(event)
        return self._create_decorator(check)(func)