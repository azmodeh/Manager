from sqlalchemy import Column, BigInteger, Text, Boolean
from app.models.base import Base


class Groups(Base):
    """Groups registry model."""
    
    __tablename__ = "groups"
    
    chat_id = Column(BigInteger, primary_key=True)
    title = Column(Text)
    approved = Column(Boolean, default=False)
    pending_approval = Column(Boolean, default=True)