import pytest
from pathlib import Path
from jarvis.tools.windows_tool import WindowsTool
from jarvis.tools.filesystem_tool import FilesystemTool
from jarvis.tools.dictation_tool import clean_dictated_text


def test_dictation_cleaner():
    raw = "um can you like send me that form by today, actually I mean tomorrow?"
    cleaned = clean_dictated_text(raw)
    assert "um" not in cleaned.lower()
    assert "like" not in cleaned.lower()
    assert "tomorrow" in cleaned.lower()
    assert cleaned[0].isupper()


def test_filesystem_tool_create_and_find(tmp_path):
    fs = FilesystemTool()
    fs.search_roots = [tmp_path]

    # Create file
    create_res = fs.create_file("my_project_notes.txt", "Notes content", str(tmp_path))
    assert create_res.is_success()
    assert (tmp_path / "my_project_notes.txt").exists()

    # Find file
    find_res = fs.find_files("notes")
    assert find_res.is_success()
    assert len(find_res.data["matches"]) >= 1


def test_windows_tool_aliases():
    win = WindowsTool()
    # Check volume controls
    res_vol = win.execute("volume_up")
    assert res_vol.is_success()
    assert "Volume" in res_vol.message
