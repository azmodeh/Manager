from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config_loader import ConfigLoader
from app.models.base import Base

config = ConfigLoader().load_yaml("env.yml")["database"]

engine = create_async_engine(config["url"], echo=config["echo"])
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


def get_session() -> AsyncSession:
    """Get database session."""
    return AsyncSessionLocal()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)