import subprocess
import sys
from pathlib import Path
from typing import Dict, Any
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def load_config() -> Dict[str, Any]:
    """Load launcher configuration.
    
    Returns:
        Configuration dictionary
    """
    config_path = Path("data/config/launcher.yml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_venv(config: Dict[str, Any]) -> None:
    """Create virtual environment.
    
    Args:
        config: Launcher configuration
    """
    venv_path = Path(config["paths"]["venv"])
    if not venv_path.exists():
        msg = config["messages"]["creating_venv"]
        style = config["styles"]["info"]
        console.print(Panel(msg, style=style))
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)])
        
        icon = config["icons"]["success"]
        msg = config["messages"]["venv_created"]
        style = config["styles"]["success"]
        console.print(f"{icon} {msg}", style=style)


def install_requirements(config: Dict[str, Any]) -> None:
    """Install requirements in virtual environment.
    
    Args:
        config: Launcher configuration
    """
    venv_python = Path(config["paths"]["venv_python_windows"])
    requirements_path = Path(config["paths"]["requirements"])
    
    if venv_python.exists() and requirements_path.exists():
        msg = config["messages"]["installing_requirements"]
        style = config["styles"]["info"]
        console.print(Panel(msg, style=style))
        subprocess.run([
            str(venv_python), 
            "-m", 
            "pip", 
            "install", 
            "-r", 
            str(requirements_path)
        ])
        
        icon = config["icons"]["success"]
        msg = config["messages"]["requirements_installed"]
        style = config["styles"]["success"]
        console.print(f"{icon} {msg}", style=style)


def run_application(config: Dict[str, Any]) -> None:
    """Run the main application.
    
    Args:
        config: Launcher configuration
    """
    venv_python = Path(config["paths"]["venv_python_windows"])
    
    if venv_python.exists():
        msg = config["messages"]["starting_app"]
        style = config["styles"]["panel"]
        console.print(Panel(msg, style=style))
        subprocess.run([str(venv_python), "-m", "app.main"])
    else:
        icon = config["icons"]["error"]
        msg = config["messages"]["venv_not_found"]
        style = config["styles"]["error"]
        console.print(f"{icon} {msg}", style=style)


def main() -> None:
    """Main launcher function."""
    config = load_config()
    
    icon = config["icons"]["banner"]
    msg = config["messages"]["banner"]
    banner = Text(f"{icon} {msg}", style=config["styles"]["banner"])
    console.print(Panel(banner, style=config["styles"]["panel"]))
    
    create_venv(config)
    install_requirements(config)
    run_application(config)


if __name__ == "__main__":
    main()
