from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists, delete
from app.models.sudo_user import SudoUser
from app.core.db import get_session


class SudoRepository:
    """Repository for sudo users operations."""
    
    async def is_sudo(self, user_id: int) -> bool:
        """Check if user is sudo admin."""
        async with get_session() as session:
            result = await session.execute(
                select(exists().where(SudoUser.user_id == user_id))
            )
            return result.scalar()
    
    async def add_sudo(self, user_id: int) -> bool:
        """Add user as sudo admin."""
        async with get_session() as session:
            try:
                session.add(SudoUser(user_id=user_id))
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                return False
    
    async def remove_sudo(self, user_id: int) -> bool:
        """Remove user from sudo admins."""
        async with get_session() as session:
            result = await session.execute(
                delete(SudoUser).where(SudoUser.user_id == user_id)
            )
            await session.commit()
            return result.rowcount > 0
    
    async def get_all_sudos(self) -> List[int]:
        """Get all sudo user IDs."""
        async with get_session() as session:
            result = await session.execute(select(SudoUser.user_id))
            return result.scalars().all()