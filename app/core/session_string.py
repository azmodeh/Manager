import asyncio
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from app.core.config_loader import ConfigLoader
from app.core.logger import MessageLogger

logger = MessageLogger(__name__)


async def generate_session_string() -> str:
    """Generate session string for userbot."""
    try:
        config = ConfigLoader().load_yaml("env.yml")["telegram"]
        
        client = TelegramClient(
            StringSession(),
            config["api_id"],
            config["api_hash"]
        )
        
        await client.start(phone=config.get("phone_number"))
        
        if not client.session:
            raise ValueError("Session not created")
        
        session_string = client.session.save()
        await client.disconnect()
        
        logger.info("session_string_generated")
        return session_string
        
    except Exception as e:
        logger.error("session_generation_failed", error=str(e))
        raise


async def main() -> None:
    """Main function for session string generation."""
    session_string = await generate_session_string()
    print(f"Session String: {session_string}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())