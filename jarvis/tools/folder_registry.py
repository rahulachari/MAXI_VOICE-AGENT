"""
JARVIS Folder Alias Registry & Path Resolver
Cross-platform resolver for user folders (Downloads, Desktop, Documents, Screenshots, etc.)
with dynamic OS screenshot detection, sandbox enforcement, and extensible local aliases.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class FolderRegistry:
    def __init__(self):
        self.home_dir = Path.home().resolve()
        self.alias_file = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "folder_aliases.json"
        self._custom_aliases: Dict[str, str] = self._load_custom_aliases()

    def _load_custom_aliases(self) -> Dict[str, str]:
        if self.alias_file.exists():
            try:
                with open(self.alias_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_custom_alias(self, alias_name: str, folder_path: str) -> bool:
        """Persists a new user-defined folder alias (e.g. 'projects' -> 'D:/Work/Projects')."""
        try:
            resolved = Path(folder_path).resolve()
            if not resolved.exists() or not resolved.is_dir():
                return False
            self._custom_aliases[alias_name.lower().strip()] = str(resolved)
            with open(self.alias_file, "w", encoding="utf-8") as f:
                json.dump(self._custom_aliases, f, indent=2)
            return True
        except Exception:
            return False

    def get_screenshot_folder(self) -> Path:
        """
        Dynamically detects the actual screenshot folder from the OS.
        Does NOT guess a hardcoded path.
        """
        if sys.platform == "darwin":
            try:
                out = subprocess.check_output(
                    ["defaults", "read", "com.apple.screencapture", "location"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()
                if out and os.path.exists(out):
                    return Path(out).resolve()
            except Exception:
                pass
            # macOS default screenshot location is Desktop
            return (self.home_dir / "Desktop").resolve()

        elif sys.platform == "win32":
            # Windows: Check registry for configured Screenshots folder
            try:
                import winreg
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                    # Windows Screenshots folder GUID
                    val, _ = winreg.QueryValueEx(key, "{B7BEDE81-DF94-4782-A1A4-4C0D72DC392E}")
                    expanded = os.path.expandvars(val)
                    if os.path.exists(expanded):
                        return Path(expanded).resolve()
            except Exception:
                pass

            # Fallback 1: Pictures\Screenshots
            default_win = self.home_dir / "Pictures" / "Screenshots"
            if default_win.exists():
                return default_win.resolve()

            # Fallback 2: OneDrive Pictures Screenshots if OneDrive is active
            onedrive_win = self.home_dir / "OneDrive" / "Pictures" / "Screenshots"
            if onedrive_win.exists():
                return onedrive_win.resolve()

            return default_win

        else:
            # Linux / FreeDesktop XDG fallback
            xdg_pics = os.environ.get("XDG_PICTURES_DIR", str(self.home_dir / "Pictures"))
            screen_dir = Path(xdg_pics) / "Screenshots"
            return screen_dir if screen_dir.exists() else Path(xdg_pics)

    def resolve_folder(self, query: str) -> Tuple[Optional[Path], Optional[str]]:
        """
        Resolves a spoken folder phrase (e.g. 'downloads', 'screenshots', 'desktop')
        to an actual validated Path object.
        Returns (Path, error_message).
        """
        clean_q = query.lower().strip()
        # Strip common voice noise words like "the video file", "my screenshot folder"
        clean_q = clean_q.replace("my ", "").replace("the ", "").replace(" folder", "").replace(" directory", "").replace(" files", "").replace(" file", "").strip()

        # 1. Check custom user aliases
        if clean_q in self._custom_aliases:
            target = Path(self._custom_aliases[clean_q]).resolve()
            if target.exists() and target.is_dir():
                return target, None

        # 2. Standard well-known folders
        if clean_q in ["screenshot", "screenshots", "screen shot", "screen shots"]:
            target = self.get_screenshot_folder()
            if not target.exists():
                try:
                    target.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
            return target, None

        if clean_q in ["download", "downloads"]:
            return (self.home_dir / "Downloads").resolve(), None

        if clean_q in ["desktop", "the desktop"]:
            return (self.home_dir / "Desktop").resolve(), None

        if clean_q in ["document", "documents", "docs"]:
            return (self.home_dir / "Documents").resolve(), None

        if clean_q in ["picture", "pictures", "photo", "photos", "images"]:
            return (self.home_dir / "Pictures").resolve(), None

        if clean_q in ["video", "videos"]:
            vid_dir = (self.home_dir / "Movies") if sys.platform == "darwin" else ((self.home_dir / "Videos" / "videos") if (self.home_dir / "Videos" / "videos").exists() else (self.home_dir / "Videos"))
            return vid_dir.resolve(), None

        if clean_q in ["movie", "movies", "film", "films"]:
            movie_dir = (self.home_dir / "Movies") if sys.platform == "darwin" else ((self.home_dir / "Videos" / "movies") if (self.home_dir / "Videos" / "movies").exists() else (self.home_dir / "Videos"))
            return movie_dir.resolve(), None

        if clean_q in ["music", "songs"]:
            return (self.home_dir / "Music").resolve(), None

        if clean_q in ["home", "user profile", "user home"]:
            return self.home_dir, None

        # 3. Dynamic search within user home directory
        for search_root in [self.home_dir, self.home_dir / "Desktop", self.home_dir / "Documents"]:
            if not search_root.exists():
                continue
            try:
                for child in search_root.iterdir():
                    if child.is_dir() and child.name.lower() == clean_q:
                        # Validate security sandbox
                        valid, err = self.validate_sandbox(child)
                        if not valid:
                            return None, err
                        return child.resolve(), None
            except Exception:
                pass

        return None, f"I couldn't find a folder matching '{query}' in your files."

    def validate_sandbox(self, path: Path) -> Tuple[bool, Optional[str]]:
        """
        Enforces security sandbox constraints:
        - Must be within user's home directory or an explicitly saved user alias.
        - Arbitrary system paths (/, C:\\Windows, C:\\Program Files) are refused.
        - Path traversal (..) is prevented.
        """
        try:
            resolved = path.resolve()
        except Exception:
            return False, "Invalid folder path."

        # Check if within user home
        try:
            resolved.relative_to(self.home_dir)
            return True, None
        except ValueError:
            pass

        # Check if in an explicitly registered custom user alias
        for custom_path in self._custom_aliases.values():
            try:
                resolved.relative_to(Path(custom_path).resolve())
                return True, None
            except ValueError:
                pass

        # Refuse system paths
        return False, "Browsing system folders outside your user profile is restricted for security."

    def list_folder_contents(self, path: Path, limit: int = 15) -> List[Dict[str, any]]:
        """
        Lists folder contents (name, is_dir, size_formatted, modified_str, icon).
        Sorted with subdirectories first, then most recently modified files.
        """
        items = []
        if not path.exists() or not path.is_dir():
            return items

        try:
            import datetime
            entries = list(path.iterdir())
            # Sort: directories first, then latest modified
            entries.sort(key=lambda e: (not e.is_dir(), -e.stat().st_mtime if e.exists() else 0))

            for entry in entries[:limit]:
                try:
                    stat = entry.stat()
                    is_dir = entry.is_dir()
                    
                    # File size
                    if is_dir:
                        size_str = "Folder"
                    else:
                        size_bytes = stat.st_size
                        if size_bytes < 1024:
                            size_str = f"{size_bytes} B"
                        elif size_bytes < 1024 * 1024:
                            size_str = f"{size_bytes / 1024:.1f} KB"
                        else:
                            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

                    # Modified date
                    mod_dt = datetime.datetime.fromtimestamp(stat.st_mtime)
                    today = datetime.datetime.today()
                    if mod_dt.date() == today.date():
                        mod_str = mod_dt.strftime("Today %I:%M %p")
                    elif mod_dt.date() == (today - datetime.timedelta(days=1)).date():
                        mod_str = mod_dt.strftime("Yesterday %I:%M %p")
                    else:
                        mod_str = mod_dt.strftime("%b %d, %Y")

                    # Icon selection
                    ext = entry.suffix.lower()
                    if is_dir:
                        icon = "📁"
                    elif ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"]:
                        icon = "🖼️"
                    elif ext in [".pdf"]:
                        icon = "📕"
                    elif ext in [".doc", ".docx", ".txt", ".md", ".rtf"]:
                        icon = "📄"
                    elif ext in [".mp3", ".wav", ".flac", ".m4a", ".aac"]:
                        icon = "🎵"
                    elif ext in [".mp4", ".mov", ".mkv", ".avi", ".webm"]:
                        icon = "🎬"
                    elif ext in [".zip", ".rar", ".7z", ".tar", ".gz"]:
                        icon = "📦"
                    elif ext in [".py", ".js", ".ts", ".html", ".css", ".json"]:
                        icon = "💻"
                    else:
                        icon = "📄"

                    items.append({
                        "name": entry.name,
                        "path": str(entry.resolve()),
                        "is_dir": is_dir,
                        "size": size_str,
                        "modified": mod_str,
                        "icon": icon,
                    })
                except Exception:
                    continue

        except Exception as e:
            print(f"[FolderRegistry] Error listing folder {path}: {e}")

        return items


# Global singleton instance
folder_registry = FolderRegistry()
