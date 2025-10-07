#!/usr/bin/env python3
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.utils.text_loader import text_loader
    from app.utils.config_loader import config_loader
    from app.utils.keyboard_builder import keyboard_builder
    from app.utils.formatter import message_formatter
    
    print("✅ All imports successful")
    
    # Test text loading
    welcome_text = text_loader.get_text("ui.welcome.title")
    print(f"✅ Text loading works: {welcome_text}")
    
    # Test emoji loading
    online_emoji = text_loader.get_emoji("status.online")
    print(f"✅ Emoji loading works: {online_emoji}")
    
    # Test config loading
    telegram_config = config_loader.get_telegram_config()
    print(f"✅ Config loading works: API ID = {telegram_config['api_id']}")
    
    print("\n🎉 ArisenManager setup is complete and ready to launch!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)