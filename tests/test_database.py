import pytest
import os
from unittest.mock import patch
from src.server.database import Database


@pytest.fixture
def db(tmp_path):
    """
    Fixture to create a DB instance using a temporary file.
    Using a file ensures persistence across connection open/close calls.
    """
    # tmp_path е вграден фикчър на pytest, който създава временна папка
    db_file = tmp_path / "test_db.sqlite"

    with patch('src.server.database.DB_PATH', str(db_file)):
        database = Database()
        yield database


def test_create_tables(db):
    """Ensure tables are created."""
    conn = db.get_connection()
    cursor = conn.cursor()

    tables = ["users", "friends", "friend_requests", "groups",
              "group_members", "public_rooms", "messages"]

    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        assert cursor.fetchone() is not None
    conn.close()


def test_register_login(db):
    assert db.register_user("ivan", "pass123") == "success"
    # Duplicate
    assert db.register_user("ivan", "pass123") == "taken"

    assert db.check_login("ivan", "pass123") is True
    assert db.check_login("ivan", "wrongpass") is False
    assert db.check_login("peter", "pass123") is False


def test_friend_request_flow(db):
    db.register_user("A", "p")
    db.register_user("B", "p")

    # 1. Send request
    assert db.send_friend_request("A", "B") == "success"
    assert db.send_friend_request("A", "B") == "already_sent"
    assert db.send_friend_request("A", "C") == "not_found"
    assert db.send_friend_request("A", "A") == "error"

    # 2. Check pending
    assert db.get_pending_requests("B") == ["A"]

    # 3. Handle request (Accept)
    db.handle_request("A", "B", "accept")

    friends_a = db.get_friends_list("A")
    friends_b = db.get_friends_list("B")
    assert "B" in friends_a
    assert "A" in friends_b

    # 4. Try sending request again
    assert db.send_friend_request("A", "B") == "already_friends"


def test_groups(db):
    db.register_user("Creator", "p")
    db.register_user("Joiner", "p")

    assert db.create_group("Group1", "Creator") is True
    assert db.create_group("Group1", "Joiner") is False  # Duplicate name

    assert db.join_group("Group1", "Joiner") is True
    assert db.join_group("NonExistent", "Joiner") is False

    members = db.get_group_members("Group1")
    assert "Creator" in members
    assert "Joiner" in members

    user_groups = db.get_user_groups("Creator")
    assert "Group1" in user_groups


def test_public_rooms(db):
    assert db.create_public_room("Room1", "fun", "Creator") is True
    assert db.create_public_room("Room1", "fun", "Creator") is False

    rooms = db.get_public_rooms()
    assert ("Room1", "fun") in rooms


def test_messages_history(db):
    db.store_message("A", "B", "encrypted_blob")
    db.store_message("B", "A", "reply_blob")

    history = db.get_chat_history("A", "B")
    assert len(history) == 2
    assert history[0]["sender"] == "A"
    assert history[0]["text"] == "encrypted_blob"
    assert history[1]["sender"] == "B"

    # Test group history
    db.store_message("A", "#Group", "hi group")
    group_hist = db.get_chat_history("A", "#Group")
    assert len(group_hist) == 1
    assert group_hist[0]["to"] == "#Group"
