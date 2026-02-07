"""
Client network module. Handles socket connections, authentication,
encryption integration, and background listening threads.
"""

import socket
import threading
from typing import Callable, Tuple, Optional, Dict, Any, List, cast
from src.common.protocol import HOST, PORT, send_json, receive_json
from src.common.crypto_utils import CryptoManager


class NetworkClient:
    """
    Handles all network communications for the client.
    Manages connection, authentication, encryption, and background listening.
    """

    def __init__(self,
                 on_msg_callback: Callable[[Dict[str, Any]], None],
                 on_data_callback: Callable[[List[str], List[str], List[str],
                                             List[str], List[Tuple[str, str]]], None],
                 on_history_callback: Callable[[str, List[Dict[str, Any]]], None]) -> None:
        self.sock: Optional[socket.socket] = None
        self.username: str = ""
        self.on_msg: Callable = on_msg_callback
        self.on_data: Callable = on_data_callback
        self.on_history: Callable = on_history_callback
        self.running: bool = False
        self.crypto: Optional[CryptoManager] = None

    def connect(self, username: str, password: str,
                is_register: bool = False) -> Tuple[bool, str]:
        """
        Connects to the server, sends login/register request, and initializes crypto.
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))

            clean = username.strip()
            action = "register" if is_register else "login"
            send_json(self.sock, {
                "action": action,
                "username": clean,
                "password": password
            })

            resp = receive_json(self.sock)

            if resp and resp.get("status") == "success":
                key = resp.get("key")
                if key and isinstance(key, str):
                    self.crypto = CryptoManager(key.encode('utf-8'))

                if not is_register:
                    self.username = clean
                    self.running = True
                    threading.Thread(target=self.listen, daemon=True).start()
                    self.refresh_data()
                return True, str(resp.get("msg", "OK"))

            if self.sock:
                self.sock.close()
            msg = str(resp.get("msg", "Error")) if resp else "Connection closed"
            return False, msg

        except Exception as e:  # pylint: disable=broad-exception-caught
            return False, str(e)

    def refresh_data(self) -> None:
        """Requests updated data (friends, rooms, active users) from server."""
        if self.running and self.sock:
            send_json(self.sock, {"action": "get_data"})

    def get_chat_history(self, target: str) -> None:
        """Requests chat history for a specific target (user or group)."""
        if self.running and self.sock:
            send_json(self.sock, {"action": "get_history", "target": target})

    def send_friend_request(self, t: str) -> None:
        """Sends a friend request to target."""
        if self.running and self.sock:
            send_json(self.sock, {"action": "send_friend_request", "target": t.strip()})

    def handle_request(self, s: str, d: str) -> None:
        """Accepts or declines a friend request."""
        if self.running and self.sock:
            send_json(self.sock, {"action": "handle_request", "sender": s, "decision": d})

    def create_group(self, n: str) -> None:
        """Creates a private group."""
        n = n.strip()
        n = "#" + n if not n.startswith("#") else n
        if self.running and self.sock:
            send_json(self.sock, {"action": "create_group", "group_name": n})

    def join_group(self, n: str) -> None:
        """Joins a private group."""
        n = n.strip()
        n = "#" + n if not n.startswith("#") else n
        if self.running and self.sock:
            send_json(self.sock, {"action": "join_group", "group_name": n})

    def create_public_room(self, n: str, t: str) -> None:
        """Creates a public room with tags."""
        n = n.strip()
        n = "&" + n if not n.startswith("&") else n
        if self.running and self.sock:
            send_json(self.sock, {
                "action": "create_public_room",
                "room_name": n,
                "tags": t.strip()
            })

    def send_message(self, recipient: str, text: str) -> None:
        """Encrypts and sends a message to the recipient."""
        if self.running and text and self.sock and self.crypto:
            encrypted = self.crypto.encrypt_message(text)
            send_json(self.sock, {"action": "msg", "to": recipient, "text": encrypted})

    def listen(self) -> None:
        """Background loop to receive messages and updates from server."""
        while self.running and self.sock:
            data = receive_json(self.sock)
            if not data:
                break

            action = data.get("action")

            if action == "msg":
                if self.crypto:
                    encrypted_text = str(data.get("text", ""))
                    data["text"] = self.crypto.decrypt_message(encrypted_text)
                    self.on_msg(data)

            elif action == "data_update":
                self.on_data(
                    cast(List[str], data.get("friends", [])),
                    cast(List[str], data.get("groups", [])),
                    cast(List[str], data.get("requests", [])),
                    cast(List[str], data.get("active_users", [])),
                    cast(List[Tuple[str, str]], data.get("public_rooms", []))
                )

            elif action == "history_response":
                msgs = data.get("messages", [])
                target = str(data.get("target", ""))

                if self.crypto:
                    for m in msgs:
                        enc_text = str(m.get("text", ""))
                        m["text"] = self.crypto.decrypt_message(enc_text)

                self.on_history(target, msgs)

        self.running = False
        if self.sock:
            self.sock.close()
