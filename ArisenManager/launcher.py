import os
import sys
import subprocess
import venv
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

class ArisenLauncher:
    def __init__(self) -> None:
        self.base_path = Path(__file__).parent
        self.config = self._load_config()
        self.texts = self._load_texts()
        self.venv_path = self.base_path / self.config["paths"]["venv_dir"]
        self.requirements_path = self.base_path / self.config["paths"]["requirements_file"]
    
    def _load_config(self) -> dict:
        config_file = self.base_path / "data" / "config" / "launcher.yml"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_texts(self) -> dict:
        text_file = self.base_path / self.config["paths"]["text_file"]
        if text_file.exists():
            with open(text_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _get_text(self, key: str, **kwargs) -> str:
        keys = key.split(".")
        value = self.texts.get("errors", {})
        for k in keys:
            value = value.get(k, {})
        if isinstance(value, str):
            return value.format(**kwargs)
        return ""
    
    def display_banner(self) -> None:
        banner_char = self.config["display"]["banner_char"]
        banner_length = self.config["display"]["banner_length"]
        banner_line = banner_char * banner_length
        
        logger.info(banner_line)
        logger.info(self._get_text("launcher.banner.display"))
        logger.info(banner_line)
    
    def create_virtual_environment(self) -> bool:
        try:
            if not self.venv_path.exists():
                logger.info(self._get_text("launcher.venv.creating"))
                venv.create(self.venv_path, with_pip=True)
                logger.info(self._get_text("launcher.venv.created"))
            else:
                logger.info(self._get_text("launcher.venv.exists"))
            return True
        except Exception as e:
            logger.error(self._get_text("launcher.venv.error", error=str(e)))
            return False
    
    def install_requirements(self) -> bool:
        try:
            platform_config = self.config["platform"]
            if os.name == platform_config["windows"]["name"]:
                pip_path = self.venv_path / platform_config["windows"]["pip_exe"]
            else:
                pip_path = self.venv_path / platform_config["unix"]["pip_exe"]
            
            logger.info(self._get_text("launcher.requirements.installing"))
            
            install_cmd = self.config["commands"]["pip_install"]
            cmd = [str(pip_path)] + install_cmd + [str(self.requirements_path)]
            
            result = subprocess.run(
                cmd,
                capture_output=self.config["subprocess"]["capture_output"],
                text=self.config["subprocess"]["text_encoding"]
            )
            
            if result.returncode == 0:
                logger.info(self._get_text("launcher.requirements.success"))
                return True
            else:
                logger.error(self._get_text("launcher.requirements.error", error=result.stderr))
                return False
        except Exception as e:
            logger.error(self._get_text("launcher.requirements.exception", error=str(e)))
            return False
    
    def run_application(self) -> None:
        try:
            platform_config = self.config["platform"]
            if os.name == platform_config["windows"]["name"]:
                python_path = self.venv_path / platform_config["windows"]["python_exe"]
            else:
                python_path = self.venv_path / platform_config["unix"]["python_exe"]
            
            logger.info(self._get_text("launcher.app.starting"))
            
            module_cmd = self.config["commands"]["python_module"]
            main_module = self.config["paths"]["main_module"]
            cmd = [str(python_path)] + module_cmd + [main_module]
            
            subprocess.run(cmd, cwd=str(self.base_path))
            
        except Exception as e:
            logger.error(self._get_text("launcher.app.error", error=str(e)))
    
    def launch(self) -> None:
        self.display_banner()
        
        if not self.create_virtual_environment():
            return
        
        if not self.install_requirements():
            return
        
        self.run_application()

if __name__ == "__main__":
    launcher = ArisenLauncher()
    launcher.launch()