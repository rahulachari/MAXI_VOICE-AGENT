"""
JARVIS File System Tool
Searches and manages files across Windows user directories with safety confirmation.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from .base import BaseTool, ToolResult


class FilesystemTool(BaseTool):
    name = "FilesystemTool"
    description = "Searches, opens, and manages files and directories."

    def __init__(self):
        self.search_roots = [
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home(),
        ]

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "find_file":
            query = kwargs.get("query", "")
            return self.find_files(query)

        elif action == "open_file":
            query = kwargs.get("query", "")
            return self.open_file(query)

        elif action == "open_folder":
            folder = kwargs.get("folder", "")
            return self.open_folder(folder)

        elif action == "create_folder":
            folder_name = kwargs.get("name", "")
            location = kwargs.get("location", "Desktop")
            return self.create_folder(folder_name, location)

        elif action == "create_file":
            file_name = kwargs.get("name", "")
            content = kwargs.get("content", "")
            location = kwargs.get("location", "Desktop")
            return self.create_file(file_name, content, location)

        elif action == "delete_file":
            target = kwargs.get("target", "")
            confirmed = kwargs.get("confirmed", False)
            return self.delete_file(target, confirmed)

        return ToolResult(status="FAILED", message=f"Unknown filesystem action: {action}")

    def find_files(self, query: str, limit: int = 5) -> ToolResult:
        if not query:
            return ToolResult(status="FAILED", message="Please specify a filename to search for.")

        matches: List[Path] = []
        clean_q = query.lower().strip()

        for root in self.search_roots:
            if not root.exists():
                continue
            try:
                for path in root.glob(f"*{clean_q}*"):
                    if path.is_file() and path not in matches:
                        matches.append(path)
                    if len(matches) >= limit:
                        break
            except Exception:
                pass
            if len(matches) >= limit:
                break

        if not matches:
            return ToolResult(status="SUCCESS", message=f"No files matching '{query}' were found.", data={"matches": []})

        if len(matches) == 1:
            return ToolResult(
                status="SUCCESS",
                message=f"Found {matches[0].name}.",
                data={"matches": [str(p) for p in matches]},
            )

        names = ", ".join(m.name for m in matches[:3])
        return ToolResult(
            status="REQUIRES_CLARIFICATION",
            message=f"I found multiple files: {names}. Which one do you mean?",
            data={"matches": [str(p) for p in matches]},
        )

    def open_file(self, query: str) -> ToolResult:
        res = self.find_files(query, limit=2)
        matches = res.data.get("matches", [])

        if not matches:
            return ToolResult(status="FAILED", message=f"Could not find any file named '{query}'.")

        if len(matches) > 1:
            return res  # returns clarification

        target_file = matches[0]
        try:
            os.startfile(target_file)
            name = Path(target_file).name
            return ToolResult(status="SUCCESS", message=f"Opened {name}.", data={"file": target_file})
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Failed to open file: {e}", error=str(e))

    def open_folder(self, folder: str) -> ToolResult:
        clean_name = folder.lower().strip()

        # Well-known system folders
        folder_map = {
            "downloads": Path.home() / "Downloads",
            "documents": Path.home() / "Documents",
            "pictures": Path.home() / "Pictures",
            "screenshots": Path.home() / "Pictures" / "Screenshots",
            "videos": Path.home() / "Videos",
            "movies": Path.home() / "Videos",
            "music": Path.home() / "Music",
            "desktop": Path.home() / "Desktop",
            "home": Path.home(),
            "appdata": Path.home() / "AppData",
            "onedrive": Path.home() / "OneDrive",
            "3d objects": Path.home() / "3D Objects",
        }

        target = folder_map.get(clean_name)

        # If not in the map, search common directories for a matching folder
        if not target:
            search_dirs = [
                Path.home() / "Desktop",
                Path.home() / "Documents",
                Path.home() / "Downloads",
                Path.home() / "Videos",
                Path.home() / "Pictures",
                Path.home() / "Music",
                Path.home(),
            ]
            for search_root in search_dirs:
                if not search_root.exists():
                    continue
                try:
                    for child in search_root.iterdir():
                        if child.is_dir() and child.name.lower() == clean_name:
                            target = child
                            break
                except Exception:
                    pass
                if target:
                    break

        if not target:
            return ToolResult(status="FAILED", message=f"I couldn't find a folder named '{folder}' on your system.")

        try:
            if not target.exists():
                target.mkdir(parents=True, exist_ok=True)
            os.startfile(str(target))
            return ToolResult(status="SUCCESS", message=f"Opened your {folder.capitalize()} folder.", data={"folder": str(target)})
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Failed to open folder: {e}", error=str(e))

    def create_folder(self, folder_name: str, location: str = "Desktop") -> ToolResult:
        if not folder_name:
            return ToolResult(status="FAILED", message="Folder name cannot be empty.")

        base_dir = Path.home() / location if location.lower() != "desktop" else Path.home() / "Desktop"
        new_dir = base_dir / folder_name

        try:
            new_dir.mkdir(parents=True, exist_ok=True)
            return ToolResult(status="SUCCESS", message=f"Created folder '{folder_name}' on {location}.", data={"path": str(new_dir)})
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Could not create folder: {e}", error=str(e))

    def create_file(self, file_name: str, content: str = "", location: str = "Desktop") -> ToolResult:
        if not file_name:
            return ToolResult(status="FAILED", message="File name cannot be empty.")

        base_dir = Path.home() / location if location.lower() != "desktop" else Path.home() / "Desktop"
        new_file = base_dir / file_name

        try:
            new_file.write_text(content, encoding="utf-8")
            return ToolResult(status="SUCCESS", message=f"Created file '{file_name}'.", data={"path": str(new_file)})
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Could not create file: {e}", error=str(e))

    def delete_file(self, target: str, confirmed: bool = False) -> ToolResult:
        if not confirmed:
            return ToolResult(
                status="REQUIRES_CONFIRMATION",
                message=f"Are you sure you want to delete {target}?",
                requires_confirmation=True,
                confirmation_prompt=f"Delete file: {target}",
                data={"target": target, "action": "delete_file"},
            )

        try:
            p = Path(target)
            if p.exists() and p.is_file():
                p.unlink()
                return ToolResult(status="SUCCESS", message=f"Deleted {p.name}.")
            return ToolResult(status="FAILED", message="File does not exist.")
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Failed to delete file: {e}", error=str(e))
