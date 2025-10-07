from sqlalchemy import Column, BigInteger
from app.models.base import Base


class SudoUser(Base):
    """Sudo users model."""
    
    __tablename__ = "sudo_users"
    
    user_id = Column(BigInteger, primary_key=True)