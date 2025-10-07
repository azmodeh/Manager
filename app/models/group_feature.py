from sqlalchemy import Column, BigInteger, Text, Boolean, CheckConstraint
from app.models.base import BaseModel


class GroupFeature(BaseModel):
    """Group features model for rules and welcome messages."""
    
    __tablename__ = "group_feature"
    
    chat_id = Column(BigInteger, nullable=False)
    feature = Column(Text, nullable=False)
    enabled = Column(Boolean, nullable=False, default=False)
    text = Column(Text)
    media_kind = Column(Text)
    media_pointer = Column(Text)
    buttons_json = Column(Text)
    updated_by = Column(BigInteger)
    
    __table_args__ = (
        CheckConstraint(
            "feature IN ('rules', 'welcome')",
            name="check_feature_type"
        ),
    )