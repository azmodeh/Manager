from typing import Optional
from sqlalchemy import select, and_, exists, update
from sqlalchemy.dialects.postgresql import insert
from app.models.group_feature import GroupFeature
from app.models.groups import Groups
from app.core.db import get_session


class GroupRepository:
    """Repository for group operations."""
    
    async def get_group_feature(
        self, 
        chat_id: int, 
        feature: str
    ) -> Optional[GroupFeature]:
        """Get group feature configuration.
        
        Args:
            chat_id: Group chat ID
            feature: Feature name (rules/welcome)
            
        Returns:
            GroupFeature instance or None
        """
        async with get_session() as session:
            result = await session.execute(
                select(GroupFeature).where(
                    and_(
                        GroupFeature.chat_id == chat_id,
                        GroupFeature.feature == feature
                    )
                )
            )
            return result.scalar_one_or_none()
    
    async def upsert_group_feature(
        self,
        chat_id: int,
        feature: str,
        enabled: bool,
        text: Optional[str] = None,
        media_kind: Optional[str] = None,
        media_pointer: Optional[str] = None,
        buttons_json: Optional[str] = None,
        updated_by: Optional[int] = None
    ) -> None:
        """Create or update group feature."""
        async with get_session() as session:
            values = {
                'chat_id': chat_id,
                'feature': feature,
                'enabled': enabled,
                'text': text,
                'media_kind': media_kind,
                'media_pointer': media_pointer,
                'buttons_json': buttons_json,
                'updated_by': updated_by
            }
            
            stmt = insert(GroupFeature).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=['chat_id', 'feature'],
                set_={k: v for k, v in values.items() if v is not None or k == 'enabled'}
            )
            await session.execute(stmt)
            await session.commit()
    
    async def is_group_approved(self, chat_id: int) -> bool:
        """Check if group is approved."""
        async with get_session() as session:
            result = await session.execute(
                select(Groups.approved).where(Groups.chat_id == chat_id)
            )
            approved = result.scalar_one_or_none()
            return bool(approved) if approved is not None else False
    
    async def add_pending_group(self, chat_id: int, title: str) -> None:
        """Add group as pending approval."""
        async with get_session() as session:
            try:
                session.add(Groups(
                    chat_id=chat_id,
                    title=title,
                    approved=False,
                    pending_approval=True
                ))
                await session.commit()
            except Exception:
                await session.rollback()
    
    async def approve_group(self, chat_id: int) -> bool:
        """Approve group."""
        async with get_session() as session:
            result = await session.execute(
                update(Groups)
                .where(Groups.chat_id == chat_id)
                .values(approved=True, pending_approval=False)
            )
            await session.commit()
            return result.rowcount > 0