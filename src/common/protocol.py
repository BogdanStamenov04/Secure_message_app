"""
Module for handling network protocol operations including
sending and receiving JSON data with length-prefixed headers.
"""

import json
import socket
import struct
from typing import Optional, Dict, Any, cast

HOST: str = '127.0.0.1'
PORT: int = 5050
HEADER_SIZE: int = 4


def send_json(sock: socket.socket, data_dict: Dict[str, Any]) -> None:
    """
    Sends a dictionary as a JSON message with a length-prefixed header.

    Args:
        sock: The target socket.
        data_dict: The dictionary containing data to send.
    """
    try:
        json_data = json.dumps(data_dict, ensure_ascii=False).encode('utf-8')
        header = struct.pack('!I', len(json_data))
        sock.sendall(header + json_data)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error sending: {e}")


def receive_json(sock: socket.socket) -> Optional[Dict[str, Any]]:
    """
    Receives exactly one JSON message from the socket.

    It reads the 4-byte header to determine length, then reads the body.

    Args:
        sock: The source socket.

    Returns:
        The parsed dictionary or None if connection fails/closes.
    """
    try:
        header = sock.recv(HEADER_SIZE)
        if not header:
            return None
        msg_length = struct.unpack('!I', header)[0]

        data = b""
        while len(data) < msg_length:
            chunk = sock.recv(min(msg_length - len(data), 4096))
            if not chunk:
                return None
            data += chunk

        return cast(Dict[str, Any], json.loads(data.decode('utf-8')))
    except Exception:  # pylint: disable=broad-exception-caught
        return None
