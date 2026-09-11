import pytest
from pathlib import Path
from jarvis.storage.database import Database
from jarvis.storage.history_repository import HistoryRepository


@pytest.fixture
def temp_repo(tmp_path):
    db_path = tmp_path / "test_jarvis.db"
    db = Database(db_path)
    repo = HistoryRepository(db)
    yield repo


def test_session_and_interaction_logging(temp_repo):
    res = temp_repo.log_interaction(
        command_text="Open YouTube",
        response_text="YouTube is open.",
        tool="BrowserTool",
        action="open_youtube",
        status="SUCCESS",
    )

    assert res["session_id"] is not None
    assert res["user_message_id"] is not None
    assert res["action_id"] is not None

    # Retrieve grouped history
    grouped = temp_repo.get_grouped_history()
    assert len(grouped["TODAY"]) == 1
    item = grouped["TODAY"][0]
    assert item["command"] == "Open YouTube"
    assert item["response"] == "YouTube is open."
    assert item["tool"] == "BrowserTool"


def test_search_history(temp_repo):
    temp_repo.log_interaction("Open YouTube", "YouTube is open.")
    temp_repo.log_interaction("Launch Notepad", "Notepad is open.")
    temp_repo.log_interaction("Search Python", "Searching...")

    # Search YouTube
    yt_results = temp_repo.get_grouped_history(search_query="YouTube")
    assert len(yt_results["TODAY"]) == 1
    assert yt_results["TODAY"][0]["command"] == "Open YouTube"

    # Search Notepad
    np_results = temp_repo.get_grouped_history(search_query="Notepad")
    assert len(np_results["TODAY"]) == 1
    assert np_results["TODAY"][0]["command"] == "Launch Notepad"


def test_delete_history_item(temp_repo):
    res = temp_repo.log_interaction("Open Calculator", "Calculator is open.")
    msg_id = res["user_message_id"]

    grouped_before = temp_repo.get_grouped_history()
    assert len(grouped_before["TODAY"]) == 1

    temp_repo.delete_item(msg_id)

    grouped_after = temp_repo.get_grouped_history()
    assert len(grouped_after["TODAY"]) == 0
