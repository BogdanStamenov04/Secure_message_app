import pytest
from unittest.mock import Mock, patch
from typing import Any, Generator
from src.client.gui import MessengerApp


@pytest.fixture
def app() -> Generator[Any, None, None]:

    with patch('src.client.gui.NetworkClient') as MockClientClass:
        mock_client_instance = MockClientClass.return_value
        mock_client_instance.connect.return_value = (True, "OK")
        mock_client_instance.username = "testuser"

        application = MessengerApp()
        application.client = mock_client_instance

        def create_mock_entry() -> Mock:
            m = Mock()
            m.get.return_value = ""
            return m

        application.user_entry = create_mock_entry()
        application.pass_entry = create_mock_entry()
        application.msg_entry = create_mock_entry()
        application.add_entry = create_mock_entry()
        application.pub_name_ent = create_mock_entry()
        application.pub_tags_ent = create_mock_entry()
        application.tag_search = create_mock_entry()

        application.status_label = Mock()
        application.chat_box = Mock()
        application.chat_header = Mock()
        application.login_screen.pack_forget = Mock()

        application.my_chats_scroll = Mock()
        application.my_chats_scroll.winfo_children.return_value = []

        yield application


def test_login_success(app: Any) -> None:
    app.user_entry.get.return_value = "user"
    app.pass_entry.get.return_value = "pass"
    app.login()
    app.client.connect.assert_called_with("user", "pass")
    app.login_screen.pack_forget.assert_called()


def test_login_fail(app: Any) -> None:
    app.client.connect.return_value = (False, "Bad pass")
    app.user_entry.get.return_value = "user"
    app.login()
    app.status_label.configure.assert_called_with(text="Bad pass")


def test_register_empty_validation(app: Any) -> None:
    app.user_entry.get.return_value = ""
    app.pass_entry.get.return_value = ""
    app.register()
    app.client.connect.assert_not_called()
    app.status_label.configure.assert_called()


def test_register_success(app: Any) -> None:
    app.user_entry.get.return_value = "newuser"
    app.pass_entry.get.return_value = "pass"
    app.client.connect.return_value = (True, "Reg OK")
    app.register()
    app.client.connect.assert_called_with("newuser", "pass", True)


def test_send_message_flow(app: Any) -> None:
    app.current_chat_target = "friend"
    app.msg_entry.get.return_value = "Hello"
    app.send_msg()
    app.client.send_message.assert_called_with("friend", "Hello")
    app.msg_entry.delete.assert_called_with(0, "end")


def test_invite_and_groups(app: Any) -> None:
    app.add_entry.get.return_value = " test "
    app.send_invite()
    app.client.send_friend_request.assert_called_with("test")
    app.create_group()
    app.client.create_group.assert_called_with("test")
    app.join_group()
    app.client.join_group.assert_called_with("test")


def test_public_room_creation(app: Any) -> None:
    app.pub_name_ent.get.return_value = "room"
    app.pub_tags_ent.get.return_value = "tag"
    app.create_public_room()
    app.client.create_public_room.assert_called_with("room", "tag")


def test_select_chat(app: Any) -> None:
    app.chat_history = {"user1": "history..."}
    app.select_chat("user1")
    app.chat_header.configure.assert_called()
    app.chat_box.insert.assert_called_with("end", "history...")
    app.client.get_chat_history.assert_called_with("user1")


def test_incoming_message(app: Any) -> None:
    data = {"sender": "u1", "to": "me", "text": "hi"}
    app.client.username = "me"
    app.on_message(data)
    assert "u1" in app.chat_history
    assert "[u1]: hi" in app.chat_history["u1"]


def test_update_data_ui(app: Any) -> None:
    friends = ["f1"]
    groups = ["g1"]
    reqs = ["r1"]
    active = ["u2"]
    pub = [("room", "tag")]

    mock_child = Mock()
    app.my_chats_scroll.winfo_children.return_value = [mock_child]
    app.tag_search.get.return_value = ""

    app.update_data(friends, groups, reqs, active, pub)

    mock_child.destroy.assert_called()
    assert True
