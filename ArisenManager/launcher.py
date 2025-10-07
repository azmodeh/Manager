import os
import sys
import subprocess
import venv
from pathlib import Path
import yaml

class ArisenLauncher:
    def __init__(self) -> None:
        self.base_path = Path(__file__).parent
        self.venv_path = self.base_path / "data" / "env" / ".venv"
        self.requirements_path = self.base_path / "data" / "env" / "requirements.txt"
        self.texts = self._load_texts()
    
    def _load_texts(self) -> dict:
        text_file = self.base_path / "data" / "texts" / "launcher_en.yml"
        if text_file.exists():
            with open(text_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _get_text(self, key: str, **kwargs) -> str:
        keys = key.split(".")
        value = self.texts
        for k in keys:
            value = value.get(k, {})
        if isinstance(value, str):
            return value.format(**kwargs)
        return ""
    
    def display_banner(self) -> None:
        print("=" * 60)
        print(self._get_text("launcher.banner"))
        print("=" * 60)
    
    def create_virtual_environment(self) -> bool:
        try:
            if not self.venv_path.exists():
                print(self._get_text("launcher.venv.creating"))
                venv.create(self.venv_path, with_pip=True)
                print(self._get_text("launcher.venv.created"))
            else:
                print(self._get_text("launcher.venv.exists"))
            return True
        except Exception as e:
            print(self._get_text("launcher.venv.error", error=str(e)))
            return False
    
    def install_requirements(self) -> bool:
        try:
            if os.name == 'nt':
                pip_path = self.venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = self.venv_path / "bin" / "pip"
            
            print(self._get_text("launcher.requirements.installing"))
            
            result = subprocess.run([
                str(pip_path), "install", "-r", str(self.requirements_path)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(self._get_text("launcher.requirements.success"))
                return True
            else:
                print(self._get_text("launcher.requirements.error", error=result.stderr))
                return False
        except Exception as e:
            print(self._get_text("launcher.requirements.exception", error=str(e)))
            return False
    
    def run_application(self) -> None:
        try:
            if os.name == 'nt':
                python_path = self.venv_path / "Scripts" / "python.exe"
            else:
                python_path = self.venv_path / "bin" / "python"
            
            print(self._get_text("launcher.app.starting"))
            
            subprocess.run([str(python_path), "-m", "app.main"], cwd=str(self.base_path))
            
        except Exception as e:
            print(self._get_text("launcher.app.error", error=str(e)))
    
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
