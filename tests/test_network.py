import unittest
from unittest.mock import Mock, patch
from cryptography.fernet import Fernet  # <--- Трябва ни, за да генерираме валиден ключ
from src.client.network import NetworkClient

class TestNetworkClient(unittest.TestCase):
    def setUp(self) -> None:
        # Mock callbacks
        self.mock_on_msg = Mock()
        self.mock_on_contacts = Mock()
        self.client = NetworkClient(self.mock_on_msg, self.mock_on_contacts)

    @patch('socket.socket')
    def test_connect_success(self, mock_socket_cls) -> None:
        """Test successful connection logic."""
        mock_sock = Mock()
        mock_socket_cls.return_value = mock_sock
        
        # Генерираме ИСТИНСКИ валиден ключ, за да не гърми Fernet
        valid_key = Fernet.generate_key().decode('utf-8')
        
        # Mock server response: Success + Valid Key
        server_response = {
            "status": "success", 
            "msg": "Welcome", 
            "key": valid_key
        }
        
        # We need to mock receive_json to return this dict
        with patch('src.client.network.receive_json', return_value=server_response):
            # Тъй като connect праща данни, трябва да мокнем и send_json, за да не гърми
            with patch('src.client.network.send_json'):
                success, msg = self.client.connect("user", "pass")
            
        self.assertTrue(success, f"Connect failed with msg: {msg}")
        self.assertEqual(msg, "Welcome")
        self.assertTrue(self.client.running)
        self.assertIsNotNone(self.client.crypto) # Crypto should be initialized

    @patch('socket.socket')
    def test_connect_fail(self, mock_socket_cls) -> None:
        """Test failed connection."""
        mock_sock = Mock()
        mock_socket_cls.return_value = mock_sock
        
        server_response = {"status": "error", "msg": "Bad pass"}
        
        with patch('src.client.network.receive_json', return_value=server_response):
            with patch('src.client.network.send_json'):
                success, msg = self.client.connect("user", "pass")
            
        self.assertFalse(success)
        self.assertEqual(msg, "Bad pass")
        self.assertFalse(self.client.running)

    def test_send_message_without_connection(self) -> None:
        """Should not crash if sending without connection."""
        try:
            self.client.send_message("someone", "hello")
        except Exception:
            self.fail("send_message crashed without connection")

    def test_send_friend_request(self) -> None:
        """Test sending friend request payload."""
        # Ръчно настройваме клиента, че е "свързан"
        self.client.running = True
        self.client.sock = Mock()
        
        # Мокваме send_json, за да видим дали се вика
        with patch('src.client.network.send_json') as mock_send_json:
            self.client.send_friend_request("target_user")
            
            mock_send_json.assert_called_with(
                self.client.sock, 
                {"action": "send_friend_request", "target": "target_user"}
            )

if __name__ == '__main__':
    unittest.main()