"""
Main server module.
Handles incoming connections, routing logic, client requests,
and persistent data storage via Database.
"""

import socket
import threading
from typing import Dict, Tuple, Optional, Any
from src.common.protocol import HOST, PORT, receive_json, send_json
from src.server.database import Database
from src.common.crypto_utils import CryptoManager


class ChatServer:
    """
    Main server class. Handles incoming connections, routing logic,
    client requests, and persistent data storage via Database.
    """

    def __init__(self) -> None:
        self.server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[str, socket.socket] = {}
        self.db: Database = Database()

        # Load or generate the persistent key
        self.crypto: CryptoManager = CryptoManager()
        self.session_key: str = self.crypto.get_key_as_string()
        print(f"[SECURITY] Session key loaded: {self.session_key[:10]}...")

    def start(self) -> None:
        """Starts the server listener."""
        try:
            self.server_socket.bind((HOST, PORT))
            self.server_socket.listen()
            print(f"[SERVER] Started on {HOST}:{PORT}")
            while True:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[CRITICAL ERROR] {e}")

    def handle_client(self, conn: socket.socket, _addr: Tuple[str, int]) -> None:
        """
        Handles the lifecycle of a single client connection.
        """
        current_user: Optional[str] = None
        try:
            while True:
                req = receive_json(conn)
                if not req:
                    break

                # Trim string inputs
                self._trim_request_inputs(req)
                action = req.get("action")

                # Delegate actions to helper methods to reduce complexity
                if action == "register":
                    self._handle_register(conn, req)
                elif action == "login":
                    current_user = self._handle_login(conn, req)
                elif action == "get_data":
                    if current_user:
                        self._refresh_client_data(current_user)
                elif action == "get_history":
                    if current_user:
                        self._handle_get_history(conn, current_user, req)
                elif action == "msg":
                    if current_user:
                        self._handle_msg(conn, current_user, req)
                else:
                    # FIX: Проверяваме дали action е стринг, преди да го подадем
                    if current_user and isinstance(action, str):
                        self._handle_other_actions(current_user, req, action)

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[ERROR] {e}")
        finally:
            if current_user and current_user in self.clients:
                del self.clients[current_user]
            conn.close()

    def _trim_request_inputs(self, req: Dict[str, Any]) -> None:
        """Trims whitespace from string fields in the request."""
        fields = ["username", "target", "sender", "group_name", "room_name", "tags", "to"]
        for field in fields:
            if field in req and isinstance(req[field], str):
                req[field] = req[field].strip()

    def _handle_register(self, conn: socket.socket, req: Dict[str, Any]) -> None:
        """Handles user registration."""
        username = req.get("username", "")
        password = req.get("password", "")

        # ВАЛИДАЦИЯ: Проверяваме дали са празни
        if not username or not password:
            send_json(conn, {"status": "error", "msg": "Username and password cannot be empty!"})
            return

        result = self.db.register_user(username, password)
        if result == "success":
            send_json(conn, {"status": "success", "msg": "OK", "key": self.session_key})
        elif result == "taken":
            send_json(conn, {"status": "error", "msg": "Username taken!"})
        else:
            send_json(conn, {"status": "error", "msg": "Error."})

    def _handle_login(self, conn: socket.socket, req: Dict[str, Any]) -> Optional[str]:
        """Handles user login. Returns username if successful, else None."""
        user = req["username"]
        if self.db.check_login(user, req["password"]):
            self.clients[user] = conn
            send_json(conn, {"status": "success", "msg": "OK", "key": self.session_key})
            return str(user)

        send_json(conn, {"status": "error", "msg": "Invalid credentials"})
        return None

    def _handle_get_history(self, conn: socket.socket,
                            current_user: str, req: Dict[str, Any]) -> None:
        """Retrieves and sends chat history."""
        target = req["target"]
        history_list = self.db.get_chat_history(current_user, target)
        send_json(conn, {
            "action": "history_response",
            "target": target,
            "messages": history_list
        })

    def _handle_msg(self, _conn: socket.socket, current_user: str, req: Dict[str, Any]) -> None:
        """Handles sending messages."""
        recipient = req["to"]
        text = req["text"]

        # 1. Store in DB (History)
        self.db.store_message(current_user, recipient, text)

        # 2. Live Delivery
        if recipient.startswith("#"):
            for m in self.db.get_group_members(recipient):
                if m in self.clients and m != current_user:
                    send_json(self.clients[m], {
                        "action": "msg",
                        "sender": current_user,
                        "to": recipient,
                        "text": text
                    })

        elif recipient.startswith("&"):
            for u, s in self.clients.items():
                if u != current_user:
                    send_json(s, {
                        "action": "msg",
                        "sender": current_user,
                        "to": recipient,
                        "text": text
                    })

        elif recipient in self.clients:
            send_json(self.clients[recipient], {
                "action": "msg",
                "sender": current_user,
                "to": current_user,
                "text": text
            })

    def _handle_other_actions(self, current_user: str, req: Dict[str, Any], action: str) -> None:
        """Handles remaining authenticated actions to reduce main loop complexity."""
        if action == "send_friend_request":
            if self.db.send_friend_request(current_user, req["target"]) == "success":
                self._refresh_client_data(req["target"])
                self._refresh_client_data(current_user)

        elif action == "handle_request":
            self.db.handle_request(req["sender"], current_user, req["decision"])
            self._refresh_client_data(current_user)
            self._refresh_client_data(req["sender"])

        elif action == "create_group":
            if self.db.create_group(req["group_name"], current_user):
                self._refresh_client_data(current_user)

        elif action == "join_group":
            if self.db.join_group(req["group_name"], current_user):
                self._refresh_client_data(current_user)

        elif action == "create_public_room":
            name = req["room_name"]
            if not name.startswith("&"):
                name = "&" + name
            if self.db.create_public_room(name, req.get("tags", ""), current_user):
                self._refresh_client_data(current_user)

    def _refresh_client_data(self, username: str) -> None:
        """Compiles and sends all contact/room data to a specific user."""
        if username in self.clients:
            friends = self.db.get_friends_list(username)
            groups = self.db.get_user_groups(username)
            requests = self.db.get_pending_requests(username)
            active = list(self.clients.keys())
            pub = self.db.get_public_rooms()
            send_json(self.clients[username], {
                "action": "data_update",
                "friends": friends,
                "groups": groups,
                "requests": requests,
                "active_users": active,
                "public_rooms": pub
            })


if __name__ == "__main__":
    ChatServer().start()
