import json
import socket
import struct
from typing import Optional, Dict, Any, cast  # <--- Добавяме 'cast' тук

HOST: str = '127.0.0.1'
PORT: int = 5050
HEADER_SIZE: int = 4

def send_json(sock: socket.socket, data_dict: Dict[str, Any]) -> None:
    """Праща речник като JSON съобщение с хедър за дължина."""
    try:
        json_data = json.dumps(data_dict, ensure_ascii=False).encode('utf-8')
        header = struct.pack('!I', len(json_data))
        sock.sendall(header + json_data)
    except Exception as e:
        print(f"Error sending: {e}")

def receive_json(sock: socket.socket) -> Optional[Dict[str, Any]]:
    """Чете точно едно JSON съобщение."""
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
            
        # ИЗПОЛЗВАМЕ cast ТУК:
        # Казваме на Mypy: "Вярвай ми, това json.loads връща речник"
        return cast(Dict[str, Any], json.loads(data.decode('utf-8')))
    except Exception:
        return None