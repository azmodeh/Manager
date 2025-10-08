import asyncio
import sys
import re
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from .database import database
from .clients import bot_clients
from .session_string import session_generator
from ..handlers import register_start_help_handlers, register_admin_handlers, register_group_handlers
from ..handlers.ai_handler import register_ai_handlers
from ..handlers.text_editor import register_text_editor_handlers
from ..handlers.user_settings import register_user_settings_handlers
from ..utils.text_loader import text_loader
from ..utils.config_loader import config_loader

class ArisenManager:
    def __init__(self) -> None:
        # Fix Windows console encoding for Unicode support
        if sys.platform == "win32":
            try:
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
            except AttributeError:
                pass
        
        self.console = Console(force_terminal=True, legacy_windows=False)
        self.running = False
    
    def _safe_print(self, text: str, style: str = "default") -> None:
        """Print text safely by removing emojis on Windows"""
        if sys.platform == "win32":
            # Remove emojis and other Unicode symbols that cause issues
            text = re.sub(r'[^\x00-\x7F]+', '', text)
        try:
            self.console.print(text, style=style)
        except UnicodeEncodeError:
            # Fallback: print without style
            print(text.encode('ascii', 'ignore').decode('ascii'))
    
    def display_banner(self) -> None:
        banner = Text(text_loader.get_text("ui.banner.title", lang="en"), style="bold cyan")
        panel = Panel(banner, title=text_loader.get_text("ui.banner.subtitle", lang="en"), border_style="blue")
        self.console.print(panel)
    
    async def initialize_database(self) -> bool:
        self._safe_print(text_loader.get_text("log.startup", lang="en"), "yellow")
        return await database.connect()
    
    async def setup_sessions(self) -> tuple[Optional[str], Optional[str]]:
        import os
        from dotenv import load_dotenv
        
        # Load environment variables from .env file
        env_path = self.console._file.name if hasattr(self.console, '_file') else None
        if not env_path:
            env_path = "data/.env"
        load_dotenv(env_path)
        
        userbot_session = os.getenv("TELEGRAM_SESSION_STRING")
        apibot_session = os.getenv("TELEGRAM_SESSION_STRING")
        
        return userbot_session, apibot_session
    
    async def start_bots(self, userbot_session: str, apibot_session: str) -> bool:
        try:
            await bot_clients.start_userbot(userbot_session)
            self._safe_print(text_loader.get_text("log.userbot_online", lang="en"), "green")
            
            await bot_clients.start_apibot(apibot_session)
            self._safe_print(text_loader.get_text("log.apibot_online", lang="en"), "green")
            
            register_start_help_handlers(bot_clients.apibot)
            register_admin_handlers(bot_clients.apibot)
            register_group_handlers(bot_clients.apibot)
            register_ai_handlers(bot_clients.apibot)
            register_text_editor_handlers(bot_clients.apibot)
            register_user_settings_handlers(bot_clients.apibot)
            
            # Notify sudo
            await bot_clients.notify_sudo_online()
            
            return True
        except Exception as e:
            self._safe_print(text_loader.get_text("err.bot_start", lang="en", error=str(e)), "red")
            return False
    
    async def start(self) -> None:
        self.display_banner()
        
        if not await self.initialize_database():
            self._safe_print(text_loader.get_text("err.database_init", lang="en"), "red")
            return
        
        userbot_session, apibot_session = await self.setup_sessions()
        
        if not userbot_session or not apibot_session:
            self._safe_print(text_loader.get_text("err.session_gen", lang="en"), "red")
            return
        
        if not await self.start_bots(userbot_session, apibot_session):
            return
        
        self._safe_print(text_loader.get_text("log.ready", lang="en"), "bold green")
        self.running = True
        
        try:
            await bot_clients.apibot.run_until_disconnected()
        except KeyboardInterrupt:
            self._safe_print(text_loader.get_text("log.shutdown", lang="en"), "yellow")
        finally:
            self.running = False