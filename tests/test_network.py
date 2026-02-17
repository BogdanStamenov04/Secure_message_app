import pytest
from unittest.mock import Mock, patch
from typing import cast
from cryptography.fernet import Fernet
from src.client.network import NetworkClient


@pytest.fixture
def client() -> NetworkClient:
    return NetworkClient(Mock(), Mock(), Mock())


def test_connect_success(client: NetworkClient) -> None:
    """Test connection and login flow."""
    valid_key = Fernet.generate_key().decode('utf-8')

    with patch('socket.socket') as mock_sock_cls:
        mock_sock = Mock()
        mock_sock_cls.return_value = mock_sock

        response = {"status": "success", "msg": "OK", "key": valid_key}

        with patch('src.client.network.receive_json', return_value=response):
            with patch('src.client.network.send_json'):
                with patch('threading.Thread'):
                    success, msg = client.connect("user", "pass")

        assert success is True
        assert client.crypto is not None
        assert client.username == "user"


def test_connect_fail(client: NetworkClient) -> None:
    with patch('socket.socket'):
        response = {"status": "error", "msg": "Fail"}
        with patch('src.client.network.receive_json', return_value=response):
            with patch('src.client.network.send_json'):
                success, msg = client.connect("user", "pass")

        assert success is False
        assert msg == "Fail"


def test_send_methods(client: NetworkClient) -> None:
    """Test helper methods for sending requests."""
    client.running = True
    client.sock = Mock()
    client.crypto = Mock()
    client.crypto.encrypt_message.return_value = "enc"

    with patch('src.client.network.send_json') as mock_send:
        client.send_message("u2", "hi")
        mock_send.assert_called_with(client.sock, {"action": "msg", "to": "u2", "text": "enc"})

        client.create_group(" g1 ")
        mock_send.assert_called_with(client.sock, {"action": "create_group", "group_name": "#g1"})

        client.create_public_room(" pub ", "tag")
        mock_send.assert_called_with(
            client.sock, {"action": "create_public_room", "room_name": "&pub", "tags": "tag"})


def test_listen_loop(client: NetworkClient) -> None:
    """Test the receiving loop."""
    client.running = True
    client.sock = Mock()
    client.crypto = Mock()
    client.crypto.decrypt_message.return_value = "decrypted"

    incoming = [
        {"action": "msg", "sender": "u2", "text": "enc"},
        {"action": "data_update", "active_users": ["u2"]},
        {"action": "history_response", "target": "u2", "messages": [{"text": "enc_hist"}]},
        None  
    ]

    with patch('src.client.network.receive_json', side_effect=incoming):
        client.listen()

        cast(Mock, client.on_msg).assert_called()
        cast(Mock, client.on_data).assert_called()
        cast(Mock, client.on_history).assert_called()
