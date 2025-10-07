from sqlalchemy import Column, Boolean, Text, BigInteger
from app.models.base import BaseModel


class GlobalCommands(BaseModel):
    """Global commands configuration model."""
    
    __tablename__ = "global_commands"
    
    start_enabled = Column(Boolean, nullable=False, default=False)
    help_enabled = Column(Boolean, nullable=False, default=False)
    start_text = Column(Text, nullable=False)
    help_text = Column(Text, nullable=False)
    updated_by = Column(BigInteger)