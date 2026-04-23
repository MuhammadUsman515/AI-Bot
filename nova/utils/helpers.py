import os
import platform
import subprocess
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".nova"
TODOS_FILE = DATA_DIR / "todos.json"
NOTES_FILE = DATA_DIR / "notes.json"
CLIPBOARD_HISTORY_FILE = DATA_DIR / "clipboard_history.json"


def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def get_os() -> str:
    return platform.system().lower()


def is_linux() -> bool:
    return get_os() == "linux"


def is_windows() -> bool:
    return get_os() == "windows"


def is_mac() -> bool:
    return get_os() == "darwin"


def run_command(cmd: list[str], capture_output: bool = True) -> tuple[str, str, int]:
    try:
        result = subprocess.run(
            cmd, capture_output=capture_output, text=True, timeout=30
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}", 1
    except Exception as e:
        return "", str(e), 1


def format_bytes(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_uptime(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}h {m}m {s}s"


def load_json(path: Path) -> list | dict:
    ensure_data_dir()
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_json(path: Path, data: list | dict):
    ensure_data_dir()
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_eval(expression: str) -> str:
    allowed = set("0123456789+-*/().% ")
    if not all(c in allowed for c in expression):
        return "Error: Invalid characters in expression"
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def open_url(url: str):
    import webbrowser
    webbrowser.open(url)


def get_home_dir() -> str:
    return str(Path.home())
