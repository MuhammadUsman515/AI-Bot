import os
import shutil
import glob
import zipfile
from pathlib import Path
from datetime import datetime
from nova.utils.helpers import (
    run_command, is_linux, is_windows, is_mac,
    load_json, save_json, NOTES_FILE, CLIPBOARD_HISTORY_FILE,
    open_url
)


class DesktopFiles:

    # ── Tool Definitions ────────────────────────────────────────────────────

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "search_files",
                "description": "Search for files and folders by name, extension, or content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "File name or pattern to search"},
                        "location": {"type": "string", "description": "Directory to search in (default: home)"},
                        "file_type": {"type": "string", "description": "File extension filter (e.g. 'pdf', 'py')"},
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_folder",
                "description": "Create a new folder/directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Full path for the new folder"},
                        "name": {"type": "string", "description": "Folder name (if path is parent directory)"},
                    },
                    "required": []
                }
            },
            {
                "name": "delete_file",
                "description": "Delete a file or folder permanently",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File or folder path to delete"},
                        "permanent": {"type": "boolean", "description": "If true, permanently delete (shred)"},
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "copy_file",
                "description": "Copy a file or folder to a destination",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string", "description": "Source file/folder path"},
                        "destination": {"type": "string", "description": "Destination path"},
                    },
                    "required": ["source", "destination"]
                }
            },
            {
                "name": "move_file",
                "description": "Move or rename a file or folder",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string", "description": "Source file/folder path"},
                        "destination": {"type": "string", "description": "Destination path or new name"},
                    },
                    "required": ["source", "destination"]
                }
            },
            {
                "name": "zip_files",
                "description": "Compress files or folders into a zip archive",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "files": {"type": "array", "items": {"type": "string"}, "description": "List of file/folder paths"},
                        "output_path": {"type": "string", "description": "Output zip file path"},
                    },
                    "required": ["files"]
                }
            },
            {
                "name": "unzip_files",
                "description": "Extract a zip or archive file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "archive_path": {"type": "string", "description": "Path to zip/archive file"},
                        "destination": {"type": "string", "description": "Destination folder to extract into"},
                    },
                    "required": ["archive_path"]
                }
            },
            {
                "name": "get_folder_size",
                "description": "Get the size of a folder and its contents",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Folder path to check"},
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "rename_file",
                "description": "Rename a file or folder",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Current file/folder path"},
                        "new_name": {"type": "string", "description": "New name"},
                    },
                    "required": ["path", "new_name"]
                }
            },
            {
                "name": "manage_notes",
                "description": "Create, list, view, or delete quick notes",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["add", "list", "view", "delete", "clear"],
                            "description": "Note action"
                        },
                        "content": {"type": "string", "description": "Note content (for 'add')"},
                        "note_id": {"type": "integer", "description": "Note ID (for 'view' or 'delete')"},
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "manage_clipboard",
                "description": "Get current clipboard content, copy text, or view clipboard history",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["get", "set", "history"],
                            "description": "Clipboard action"
                        },
                        "text": {"type": "string", "description": "Text to copy (for 'set')"},
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "change_wallpaper",
                "description": "Change the desktop wallpaper",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to image file"},
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "list_directory",
                "description": "List files and folders in a directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path (default: home)"},
                        "show_hidden": {"type": "boolean", "description": "Show hidden files"},
                    },
                    "required": []
                }
            },
            {
                "name": "read_file_content",
                "description": "Read and return the content of a text file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read"},
                        "lines": {"type": "integer", "description": "Number of lines to read (default: all)"},
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "open_downloads",
                "description": "Open the Downloads folder",
                "input_schema": {"type": "object", "properties": {}, "required": []}
            },
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "search_files": self.search_files,
            "create_folder": self.create_folder,
            "delete_file": self.delete_file,
            "copy_file": self.copy_file,
            "move_file": self.move_file,
            "zip_files": self.zip_files,
            "unzip_files": self.unzip_files,
            "get_folder_size": self.get_folder_size,
            "rename_file": self.rename_file,
            "manage_notes": self.manage_notes,
            "manage_clipboard": self.manage_clipboard,
            "change_wallpaper": self.change_wallpaper,
            "list_directory": self.list_directory,
            "read_file_content": self.read_file_content,
            "open_downloads": self.open_downloads,
        }

    # ── Implementations ──────────────────────────────────────────────────────

    def search_files(self, query: str, location: str = None, file_type: str = None) -> str:
        base = location or str(Path.home())
        pattern = f"*{query}*"
        if file_type:
            pattern = f"*{query}*.{file_type.lstrip('.')}"
        try:
            results = []
            for p in Path(base).rglob(pattern):
                results.append(str(p))
                if len(results) >= 20:
                    break
            if not results:
                return f"No files found matching '{query}' in {base}"
            return f"Found {len(results)} file(s):\n" + "\n".join(results)
        except Exception as e:
            return f"Search error: {e}"

    def create_folder(self, path: str = None, name: str = None) -> str:
        try:
            if path and name:
                target = Path(path) / name
            elif path:
                target = Path(path)
            elif name:
                target = Path.home() / name
            else:
                return "Please provide a folder path or name"
            target.mkdir(parents=True, exist_ok=True)
            return f"Folder created: {target}"
        except Exception as e:
            return f"Error creating folder: {e}"

    def delete_file(self, path: str, permanent: bool = False) -> str:
        try:
            p = Path(path)
            if not p.exists():
                return f"Path not found: {path}"
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return f"Deleted: {path}"
        except Exception as e:
            return f"Delete error: {e}"

    def copy_file(self, source: str, destination: str) -> str:
        try:
            src = Path(source)
            if not src.exists():
                return f"Source not found: {source}"
            dst = Path(destination)
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            return f"Copied '{source}' to '{destination}'"
        except Exception as e:
            return f"Copy error: {e}"

    def move_file(self, source: str, destination: str) -> str:
        try:
            src = Path(source)
            if not src.exists():
                return f"Source not found: {source}"
            shutil.move(str(src), destination)
            return f"Moved '{source}' to '{destination}'"
        except Exception as e:
            return f"Move error: {e}"

    def zip_files(self, files: list[str], output_path: str = None) -> str:
        try:
            if not output_path:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(Path.home() / f"archive_{ts}.zip")
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for fp in files:
                    p = Path(fp)
                    if p.is_file():
                        zf.write(p, p.name)
                    elif p.is_dir():
                        for sub in p.rglob("*"):
                            if sub.is_file():
                                zf.write(sub, sub.relative_to(p.parent))
            size = Path(output_path).stat().st_size
            return f"Archive created: {output_path} ({size // 1024} KB)"
        except Exception as e:
            return f"Zip error: {e}"

    def unzip_files(self, archive_path: str, destination: str = None) -> str:
        try:
            p = Path(archive_path)
            if not p.exists():
                return f"Archive not found: {archive_path}"
            dest = Path(destination) if destination else p.parent / p.stem
            dest.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(p) as zf:
                zf.extractall(dest)
            return f"Extracted to: {dest}"
        except Exception as e:
            return f"Unzip error: {e}"

    def get_folder_size(self, path: str) -> str:
        try:
            p = Path(path)
            if not p.exists():
                return f"Path not found: {path}"
            total = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            count = sum(1 for _ in p.rglob("*"))
            from nova.utils.helpers import format_bytes
            return f"Folder: {path}\nSize: {format_bytes(total)}\nItems: {count}"
        except Exception as e:
            return f"Error: {e}"

    def rename_file(self, path: str, new_name: str) -> str:
        try:
            p = Path(path)
            if not p.exists():
                return f"Path not found: {path}"
            new_path = p.parent / new_name
            p.rename(new_path)
            return f"Renamed to: {new_path}"
        except Exception as e:
            return f"Rename error: {e}"

    def manage_notes(self, action: str, content: str = None, note_id: int = None) -> str:
        notes = load_json(NOTES_FILE)
        if not isinstance(notes, list):
            notes = []

        if action == "add":
            if not content:
                return "Please provide note content"
            note = {"id": len(notes) + 1, "content": content, "created": datetime.now().isoformat()}
            notes.append(note)
            save_json(NOTES_FILE, notes)
            return f"Note saved (ID: {note['id']})"

        elif action == "list":
            if not notes:
                return "No notes found"
            return "\n".join([f"[{n['id']}] {n['content'][:80]}..." if len(n['content']) > 80 else f"[{n['id']}] {n['content']}" for n in notes])

        elif action == "view":
            note = next((n for n in notes if n["id"] == note_id), None)
            if not note:
                return f"Note {note_id} not found"
            return f"Note {note['id']} ({note['created'][:10]}):\n{note['content']}"

        elif action == "delete":
            before = len(notes)
            notes = [n for n in notes if n["id"] != note_id]
            save_json(NOTES_FILE, notes)
            return f"Note {note_id} deleted" if len(notes) < before else f"Note {note_id} not found"

        elif action == "clear":
            save_json(NOTES_FILE, [])
            return "All notes cleared"

        return "Unknown action"

    def manage_clipboard(self, action: str, text: str = None) -> str:
        try:
            import pyperclip
            history = load_json(CLIPBOARD_HISTORY_FILE)
            if not isinstance(history, list):
                history = []

            if action == "get":
                content = pyperclip.paste()
                if content and (not history or history[-1] != content):
                    history.append(content)
                    save_json(CLIPBOARD_HISTORY_FILE, history[-50:])
                return f"Clipboard: {content or '(empty)'}"

            elif action == "set":
                if not text:
                    return "Please provide text to copy"
                pyperclip.copy(text)
                history.append(text)
                save_json(CLIPBOARD_HISTORY_FILE, history[-50:])
                return f"Copied to clipboard: {text[:50]}..."

            elif action == "history":
                if not history:
                    return "Clipboard history is empty"
                lines = [f"[{i+1}] {item[:60]}" for i, item in enumerate(reversed(history[-10:]))]
                return "Recent clipboard history:\n" + "\n".join(lines)

        except ImportError:
            return "pyperclip not installed. Run: pip install pyperclip"
        except Exception as e:
            return f"Clipboard error: {e}"

    def change_wallpaper(self, path: str) -> str:
        p = Path(path)
        if not p.exists():
            return f"Image not found: {path}"
        try:
            if is_linux():
                uri = f"file://{p.absolute()}"
                out, err, code = run_command(
                    ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri]
                )
                if code == 0:
                    return f"Wallpaper changed to: {path}"
                run_command(["feh", "--bg-scale", str(p.absolute())])
                return f"Wallpaper changed to: {path}"
            elif is_windows():
                import ctypes
                ctypes.windll.user32.SystemParametersInfoW(20, 0, str(p.absolute()), 3)
                return f"Wallpaper changed to: {path}"
            elif is_mac():
                script = f'tell application "Finder" to set desktop picture to POSIX file "{p.absolute()}"'
                run_command(["osascript", "-e", script])
                return f"Wallpaper changed to: {path}"
        except Exception as e:
            return f"Wallpaper error: {e}"

    def list_directory(self, path: str = None, show_hidden: bool = False) -> str:
        try:
            target = Path(path) if path else Path.home()
            if not target.exists():
                return f"Path not found: {path}"
            items = []
            for p in sorted(target.iterdir()):
                if not show_hidden and p.name.startswith("."):
                    continue
                size = ""
                if p.is_file():
                    size = f" ({p.stat().st_size // 1024} KB)"
                kind = "📁" if p.is_dir() else "📄"
                items.append(f"{kind} {p.name}{size}")
            return f"Contents of {target}:\n" + "\n".join(items[:50])
        except Exception as e:
            return f"List error: {e}"

    def read_file_content(self, path: str, lines: int = None) -> str:
        try:
            p = Path(path)
            if not p.exists():
                return f"File not found: {path}"
            if p.stat().st_size > 1_000_000:
                return "File too large to read (>1MB)"
            content = p.read_text(errors="replace")
            if lines:
                content = "\n".join(content.splitlines()[:lines])
            return content
        except Exception as e:
            return f"Read error: {e}"

    def open_downloads(self) -> str:
        downloads = Path.home() / "Downloads"
        try:
            if is_linux():
                run_command(["xdg-open", str(downloads)], capture_output=False)
            elif is_windows():
                run_command(["explorer", str(downloads)], capture_output=False)
            elif is_mac():
                run_command(["open", str(downloads)], capture_output=False)
            return f"Opened Downloads: {downloads}"
        except Exception as e:
            return f"Error: {e}"
