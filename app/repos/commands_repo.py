from typing import Optional
from sqlalchemy import select
from app.models.global_commands import GlobalCommands
from app.core.db import get_session


class CommandsRepository:
    """Repository for global commands operations."""
    
    async def get_global_commands(self) -> Optional[GlobalCommands]:
        """Get global commands configuration.
        
        Returns:
            GlobalCommands instance or None
        """
        async with get_session() as session:
            result = await session.execute(
                select(GlobalCommands).order_by(GlobalCommands.id.desc())
            )
            return result.scalar_one_or_none()
    
    async def _get_or_create_config(self, session) -> GlobalCommands:
        """Get existing config or create new one within session."""
        result = await session.execute(
            select(GlobalCommands).order_by(GlobalCommands.id.desc())
        )
        config = result.scalar_one_or_none()
        
        if not config:
            config = GlobalCommands(
                start_enabled=False, start_text="",
                help_enabled=False, help_text="", updated_by=0
            )
            session.add(config)
        
        return config
    
    async def update_start_command(self, enabled: bool, text: str, updated_by: int) -> None:
        """Update start command configuration."""
        async with get_session() as session:
            config = await self._get_or_create_config(session)
            config.start_enabled = enabled
            config.start_text = text
            config.updated_by = updated_by
            await session.commit()
    
    async def update_help_command(self, enabled: bool, text: str, updated_by: int) -> None:
        """Update help command configuration."""
        async with get_session() as session:
            config = await self._get_or_create_config(session)
            config.help_enabled = enabled
            config.help_text = text
            config.updated_by = updated_by
            await session.commit()