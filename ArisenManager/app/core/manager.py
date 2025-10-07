import asyncio
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from .database import database
from .clients import bot_clients
from .session_string import session_generator
from ..handlers import register_start_help_handlers, register_admin_handlers, register_group_handlers
from ..utils.text_loader import text_loader
from ..utils.config_loader import config_loader

class ArisenManager:
    def __init__(self) -> None:
        self.console = Console()
        self.running = False
    
    def display_banner(self) -> None:
        banner = Text("ArisenManager", style="bold cyan")
        panel = Panel(banner, title="Telegram Bot Manager", border_style="blue")
        self.console.print(panel)
    
    async def initialize_database(self) -> bool:
        self.console.print(text_loader.get_text("log.startup", lang="en"), style="yellow")
        return await database.connect()
    
    async def setup_sessions(self) -> tuple[Optional[str], Optional[str]]:
        config = config_loader.load_config("env.yml")
        telegram_config = config.get("telegram", {})
        sessions = config.get("sessions", {})
        
        userbot_session = telegram_config.get("session_string") or sessions.get("userbot_session")
        apibot_session = sessions.get("apibot_session")
        
        if not userbot_session:
            self.console.print("Generating UserBot session...", style="cyan")
            userbot_session = await session_generator.generate_userbot_session()
        
        if not apibot_session:
            self.console.print("Generating API Bot session...", style="cyan")
            apibot_session = await session_generator.generate_bot_session()
        
        return userbot_session, apibot_session
    
    async def start_bots(self, userbot_session: str, apibot_session: str) -> bool:
        try:
            await bot_clients.start_userbot(userbot_session)
            self.console.print(text_loader.get_text("log.userbot_online", lang="en"), style="green")
            
            await bot_clients.start_apibot(apibot_session)
            self.console.print(text_loader.get_text("log.apibot_online", lang="en"), style="green")
            
            print("[DEBUG] Registering handlers for apibot (ONCE)")
            register_start_help_handlers(bot_clients.apibot)
            register_admin_handlers(bot_clients.apibot)
            register_group_handlers(bot_clients.apibot)
            
            handlers_count = len(bot_clients.apibot.list_event_handlers())
            print(f"[DEBUG] Total handlers registered: {handlers_count}")
            
            # Notify sudo
            await bot_clients.notify_sudo_online()
            
            return True
        except Exception as e:
            self.console.print(f"Error starting bots: {e}", style="red")
            return False
    
    async def start(self) -> None:
        self.display_banner()
        
        if not await self.initialize_database():
            self.console.print("Database initialization failed", style="red")
            return
        
        userbot_session, apibot_session = await self.setup_sessions()
        
        if not userbot_session or not apibot_session:
            self.console.print("Session generation failed", style="red")
            return
        
        if not await self.start_bots(userbot_session, apibot_session):
            return
        
        self.console.print(text_loader.get_text("log.ready", lang="en"), style="bold green")
        self.running = True
        
        try:
            await bot_clients.apibot.run_until_disconnected()
        except KeyboardInterrupt:
            self.console.print("Shutting down...", style="yellow")
        finally:
            self.running = False