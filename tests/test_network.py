import socket
from unittest.mock import Mock, patch
from cryptography.fernet import Fernet
import pytest
from src.client.network import NetworkClient


@pytest.fixture
def client():
    return NetworkClient(Mock(), Mock(), Mock())


def test_connect_success(client):
    """Test connection and login flow."""
    # Generate a valid key for the mock response
    valid_key = Fernet.generate_key().decode('utf-8')

    with patch('socket.socket') as mock_sock_cls:
        mock_sock = Mock()
        mock_sock_cls.return_value = mock_sock

        response = {"status": "success", "msg": "OK", "key": valid_key}

        with patch('src.client.network.receive_json', return_value=response):
            with patch('src.client.network.send_json'):
                # We mock threading to prevent actual thread start
                with patch('threading.Thread'):
                    success, msg = client.connect("user", "pass")

        assert success is True
        assert client.crypto is not None
        assert client.username == "user"


def test_connect_fail(client):
    with patch('socket.socket'):
        response = {"status": "error", "msg": "Fail"}
        with patch('src.client.network.receive_json', return_value=response):
            with patch('src.client.network.send_json'):
                success, msg = client.connect("user", "pass")

        assert success is False
        assert msg == "Fail"


def test_send_methods(client):
    """Test helper methods for sending requests."""
    client.running = True
    client.sock = Mock()

    # Mock crypto for send_message
    client.crypto = Mock()
    client.crypto.encrypt_message.return_value = "enc"

    with patch('src.client.network.send_json') as mock_send:
        # Message
        client.send_message("u2", "hi")
        mock_send.assert_called_with(client.sock, {"action": "msg", "to": "u2", "text": "enc"})

        # Group
        client.create_group(" g1 ")
        mock_send.assert_called_with(client.sock, {"action": "create_group", "group_name": "#g1"})

        # Public Room
        client.create_public_room(" pub ", "tag")
        mock_send.assert_called_with(
            client.sock, {"action": "create_public_room", "room_name": "&pub", "tags": "tag"})


def test_listen_loop(client):
    """Test the receiving loop."""
    client.running = True
    client.sock = Mock()
    client.crypto = Mock()
    client.crypto.decrypt_message.return_value = "decrypted"

    # Sequence of incoming messages
    incoming = [
        {"action": "msg", "sender": "u2", "text": "enc"},
        {"action": "data_update", "active_users": ["u2"]},
        {"action": "history_response", "target": "u2", "messages": [{"text": "enc_hist"}]},
        None  # Stop loop
    ]

    with patch('src.client.network.receive_json', side_effect=incoming):
        client.listen()

        # Check callbacks
        client.on_msg.assert_called()
        client.on_data.assert_called()
        client.on_history.assert_called()
