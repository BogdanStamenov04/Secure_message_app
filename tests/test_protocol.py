import unittest
import json
import struct
from unittest.mock import Mock
from src.common.protocol import send_json, receive_json, HEADER_SIZE

class TestProtocol(unittest.TestCase):
    def test_send_json(self) -> None:
        """Test sending a dictionary correctly packs header and data."""
        mock_socket = Mock()
        data: dict = {"key": "value", "cyrillic": "здравей"}
        
        send_json(mock_socket, data)
        
        # Prepare expected data
        json_bytes: bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        header: bytes = struct.pack('!I', len(json_bytes))
        
        # Check if sendall was called with header + json
        mock_socket.sendall.assert_called_with(header + json_bytes)

    def test_send_json_error(self) -> None:
        """Test send_json handles exceptions gracefully."""
        mock_socket = Mock()
        mock_socket.sendall.side_effect = Exception("Connection lost")
        
        # Should not raise exception (it prints error instead)
        try:
            send_json(mock_socket, {"a": 1})
        except Exception:
            self.fail("send_json raised exception unexpectedly")

    def test_receive_json_success(self) -> None:
        """Test receiving a valid message."""
        mock_socket = Mock()
        
        data: dict = {"test": "ok"}
        json_bytes: bytes = json.dumps(data).encode('utf-8')
        header: bytes = struct.pack('!I', len(json_bytes))
        
        # Configure mock to return header first, then body
        mock_socket.recv.side_effect = [header, json_bytes]
        
        result = receive_json(mock_socket)
        self.assertEqual(result, data)

    def test_receive_json_empty_header(self) -> None:
        """Test receiving None if connection closed at header."""
        mock_socket = Mock()
        mock_socket.recv.return_value = b"" # EOF
        
        result = receive_json(mock_socket)
        self.assertIsNone(result)

    def test_receive_json_partial_body(self) -> None:
        """Test receiving None if connection closed during body."""
        mock_socket = Mock()
        data = b'{"a": 1}'
        header = struct.pack('!I', len(data))
        
        # Return header, then nothing (connection break)
        mock_socket.recv.side_effect = [header, b""]
        
        result = receive_json(mock_socket)
        self.assertIsNone(result)

    def test_receive_json_invalid_utf8(self) -> None:
        """Test receiving invalid JSON data."""
        mock_socket = Mock()
        header = struct.pack('!I', 4)
        body = b"\xff\xff\xff\xff" # Invalid UTF-8
        
        mock_socket.recv.side_effect = [header, body]
        
        # The function catches exceptions and returns None
        result = receive_json(mock_socket)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()