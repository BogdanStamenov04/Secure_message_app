import pytest
from unittest.mock import Mock, patch, ANY
from src.server.server_main import ChatServer


@pytest.fixture
def server():
    with patch('src.server.server_main.Database') as MockDB:
        with patch('src.server.server_main.CryptoManager') as MockCrypto:
            MockCrypto.return_value.get_key_as_string.return_value = "secret_key"
            server_instance = ChatServer()
            server_instance.db = MockDB.return_value
            yield server_instance


def test_start_server(server):
    """Test socket binding and listening."""
    with patch('socket.socket') as mock_sock_cls:
        mock_sock = Mock()
        mock_sock_cls.return_value = mock_sock
        # Mock accept to raise exception to break the while True loop immediately
        mock_sock.accept.side_effect = Exception("Stop loop")

        server.server_socket = mock_sock
        server.start()

        mock_sock.bind.assert_called_with(ANY)
        mock_sock.listen.assert_called()


def test_handle_client_register_empty_fields(server):
    """Test registration with empty username or password."""
    mock_conn = Mock()
    # Scenario: Empty username
    req = {"action": "register", "username": "", "password": "123"}

    with patch('src.server.server_main.receive_json', side_effect=[req, None]):
        with patch('src.server.server_main.send_json') as mock_send:

            server.handle_client(mock_conn, ("ip", 123))

            # 1. Database should NOT be called
            server.db.register_user.assert_not_called()

            # 2. Should send error message
            mock_send.assert_called_with(mock_conn, {
                "status": "error",
                "msg": "Username and password cannot be empty!"
            })


def test_handle_client_register(server):
    mock_conn = Mock()
    req = {"action": "register", "username": " u1 ", "password": "p1"}

    with patch('src.server.server_main.receive_json', side_effect=[req, None]):
        with patch('src.server.server_main.send_json') as mock_send:
            server.db.register_user.return_value = "success"

            server.handle_client(mock_conn, ("ip", 123))

            # Check DB call (trimmed username)
            server.db.register_user.assert_called_with("u1", "p1")
            # Check response
            mock_send.assert_called_with(
                mock_conn, {"status": "success", "msg": "OK", "key": "secret_key"})


def test_handle_client_login_success(server):
    mock_conn = Mock()
    req = {"action": "login", "username": "u1", "password": "p1"}

    # FIX: Проверяваме изпратеното съобщение, а не server.clients
    # защото server.clients се чисти при disconnect (None от receive_json)
    with patch('src.server.server_main.receive_json', side_effect=[req, None]):
        with patch('src.server.server_main.send_json') as mock_send:
            server.db.check_login.return_value = True

            server.handle_client(mock_conn, ("ip", 123))

            # Проверяваме дали е изпратен успешен отговор
            mock_send.assert_called_with(
                mock_conn, {"status": "success", "msg": "OK", "key": "secret_key"})


def test_handle_client_actions(server):
    """Test messaging, history, and other actions after login."""
    mock_conn = Mock()

    requests = [
        {"action": "login", "username": "u1", "password": "p1"},
        {"action": "msg", "to": "u2", "text": "enc_txt"},
        {"action": "get_history", "target": "u2"},
        {"action": "create_group", "group_name": "g1"},
        None  # Break loop
    ]

    server.clients["u2"] = Mock()

    with patch('src.server.server_main.receive_json', side_effect=requests):
        with patch('src.server.server_main.send_json'):
            server.db.check_login.return_value = True

            server.handle_client(mock_conn, ("ip", 123))

            # Verify Msg stored
            server.db.store_message.assert_called_with("u1", "u2", "enc_txt")

            # Verify History
            server.db.get_chat_history.assert_called_with("u1", "u2")

            # Verify Group Create
            server.db.create_group.assert_called_with("g1", "u1")


def test_handle_msg_routing_public(server):
    """Test routing to public room (&room)."""
    conn1 = Mock()
    conn2 = Mock()
    server.clients = {"u1": conn1, "u2": conn2}

    req = {"action": "msg", "to": "&room", "text": "hi"}

    with patch('src.server.server_main.send_json') as mock_send:
        server._handle_msg(conn1, "u1", req)

        args, _ = mock_send.call_args
        assert args[0] == conn2
        assert args[1]["to"] == "&room"
