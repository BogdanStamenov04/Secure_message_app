import socket
import struct
import json
from unittest.mock import Mock
import pytest
from src.common.protocol import send_json, receive_json


def test_send_json_success():
    """Test successfully sending a JSON message."""
    mock_socket = Mock(spec=socket.socket)
    data = {"test": "data", "cyrillic": "здравей"}

    send_json(mock_socket, data)

    # Verify exact bytes sent
    json_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
    header = struct.pack('!I', len(json_bytes))
    expected_call = header + json_bytes

    mock_socket.sendall.assert_called_once_with(expected_call)


def test_send_json_exception(capsys):
    """Test that exceptions during send are caught and printed."""
    mock_socket = Mock(spec=socket.socket)
    mock_socket.sendall.side_effect = Exception("Connection lost")

    send_json(mock_socket, {"a": 1})

    captured = capsys.readouterr()
    assert "Error sending: Connection lost" in captured.out


def test_receive_json_success():
    """Test successfully receiving a JSON message."""
    mock_socket = Mock(spec=socket.socket)
    data = {"key": "value"}
    json_bytes = json.dumps(data).encode('utf-8')
    header = struct.pack('!I', len(json_bytes))

    # Mock recv to return header first, then body
    mock_socket.recv.side_effect = [header, json_bytes]

    result = receive_json(mock_socket)
    assert result == data


def test_receive_json_fragmented():
    """Test receiving a message that arrives in chunks."""
    mock_socket = Mock(spec=socket.socket)
    data = {"key": "long_value" * 10}
    json_bytes = json.dumps(data).encode('utf-8')
    header = struct.pack('!I', len(json_bytes))

    # Split body into two chunks
    chunk1 = json_bytes[:10]
    chunk2 = json_bytes[10:]

    mock_socket.recv.side_effect = [header, chunk1, chunk2]

    result = receive_json(mock_socket)
    assert result == data


def test_receive_json_connection_closed_header():
    """Test receiving None when connection closes at header."""
    mock_socket = Mock(spec=socket.socket)
    mock_socket.recv.return_value = b""  # Empty bytes = EOF

    assert receive_json(mock_socket) is None


def test_receive_json_connection_closed_body():
    """Test receiving None when connection closes mid-body."""
    mock_socket = Mock(spec=socket.socket)
    header = struct.pack('!I', 100)
    # Return header, then nothing
    mock_socket.recv.side_effect = [header, b""]

    assert receive_json(mock_socket) is None


def test_receive_json_exception():
    """Test handling of exceptions during receive."""
    mock_socket = Mock(spec=socket.socket)
    mock_socket.recv.side_effect = Exception("Socket error")

    assert receive_json(mock_socket) is None
