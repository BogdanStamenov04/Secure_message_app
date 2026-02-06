import socket
import threading
from typing import Dict, Tuple
from src.common.protocol import HOST, PORT, receive_json, send_json
from src.server.database import Database
from src.common.crypto_utils import CryptoManager

class ChatServer:
    def __init__(self) -> None:
        self.server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[str, socket.socket] = {} 
        self.db: Database = Database()
        
        # Генерираме динамичен ключ при старта
        self.crypto: CryptoManager = CryptoManager() 
        self.session_key: str = self.crypto.get_key_as_string()
        print(f"[SECURITY] Сесиен ключ: {self.session_key[:10]}...")

    def start(self) -> None:
        try:
            self.server_socket.bind((HOST, PORT))
            self.server_socket.listen()
            print(f"[SERVER] Стартиран на {HOST}:{PORT}")
            while True:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()
        except Exception as e:
            print(f"[CRITICAL ERROR] {e}")

    def handle_client(self, conn: socket.socket, addr: Tuple[str, int]) -> None:
        current_user = None
        try:
            while True:
                req = receive_json(conn)
                if not req: break
                
                action = req.get("action")

                if action == "register":
                    result = self.db.register_user(req["username"], req["password"])
                    if result == "success":
                        # Пращаме ключа
                        send_json(conn, {"status": "success", "msg": "OK", "key": self.session_key})
                    elif result == "taken":
                        send_json(conn, {"status": "error", "msg": "Заето име!"})
                    else:
                        send_json(conn, {"status": "error", "msg": "Грешка."})

                elif action == "login":
                    user = req["username"]
                    if self.db.check_login(user, req["password"]):
                        self.clients[user] = conn
                        current_user = user
                        # Пращаме ключа
                        send_json(conn, {"status": "success", "msg": "OK", "key": self.session_key})
                    else:
                        send_json(conn, {"status": "error", "msg": "Грешни данни"})

                elif action == "get_contacts":
                    self._refresh_contacts(current_user)

                elif action == "send_friend_request":
                    res = self.db.send_friend_request(current_user, req["target"])
                    if res == "success":
                        self._refresh_contacts(req["target"]); self._refresh_contacts(current_user)

                elif action == "handle_request":
                    self.db.handle_request(req["sender"], current_user, req["decision"])
                    self._refresh_contacts(current_user); self._refresh_contacts(req["sender"])

                elif action == "create_group":
                    if self.db.create_group(req["group_name"], current_user): self._refresh_contacts(current_user)

                elif action == "join_group":
                    if self.db.join_group(req["group_name"], current_user): self._refresh_contacts(current_user)

                elif action == "msg":
                    recipient = req["to"]
                    text = req["text"]
                    if recipient.startswith("#"):
                        for m in self.db.get_group_members(recipient):
                            if m in self.clients and m != current_user:
                                send_json(self.clients[m], {"action": "msg", "sender": current_user, "to": recipient, "text": text})
                    elif recipient in self.clients:
                        send_json(self.clients[recipient], {"action": "msg", "sender": current_user, "to": current_user, "text": text})

        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            if current_user and current_user in self.clients: del self.clients[current_user]
            conn.close()

    def _refresh_contacts(self, username: str) -> None:
        if username in self.clients:
            friends = self.db.get_friends_list(username)
            groups = self.db.get_user_groups(username)
            requests = self.db.get_pending_requests(username)
            send_json(self.clients[username], {"action": "contacts_update", "friends": friends, "groups": groups, "requests": requests})

if __name__ == "__main__":
    ChatServer().start()