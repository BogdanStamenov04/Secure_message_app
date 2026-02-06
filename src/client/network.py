import socket
import threading
from typing import Callable, Tuple, Optional, Dict, Any
from src.common.protocol import HOST, PORT, send_json, receive_json
from src.common.crypto_utils import CryptoManager

class NetworkClient:
    def __init__(self, on_msg_callback: Callable, on_contacts_callback: Callable) -> None:
        self.sock: Optional[socket.socket] = None
        self.username: str = ""
        self.on_msg: Callable = on_msg_callback
        self.on_contacts: Callable = on_contacts_callback
        self.running: bool = False
        self.crypto: Optional[CryptoManager] = None # Първоначално нямаме ключ

    def connect(self, username: str, password: str, is_register: bool = False) -> Tuple[bool, str]:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            
            action = "register" if is_register else "login"
            send_json(self.sock, {"action": action, "username": username, "password": password})
            
            resp = receive_json(self.sock)
            if resp and resp.get("status") == "success":
                # Взимаме ключа от отговора на сървъра
                server_key = resp.get("key")
                if server_key:
                    self.crypto = CryptoManager(server_key.encode('utf-8'))
                
                if not is_register:
                    self.username = username
                    self.running = True
                    threading.Thread(target=self.listen, daemon=True).start()
                    self.refresh_contacts()
                return True, resp.get("msg")
            else:
                self.sock.close()
                return False, resp.get("msg", "Грешка")
        except Exception as e:
            return False, str(e)

    def refresh_contacts(self) -> None:
        if self.running and self.sock: send_json(self.sock, {"action": "get_contacts"})

    def send_friend_request(self, target: str) -> None:
        if self.running and self.sock: send_json(self.sock, {"action": "send_friend_request", "target": target})

    def handle_request(self, sender: str, decision: str) -> None:
        if self.running and self.sock: send_json(self.sock, {"action": "handle_request", "sender": sender, "decision": decision})

    def create_group(self, name: str) -> None:
        if not name.startswith("#"): name = "#" + name
        if self.running and self.sock: send_json(self.sock, {"action": "create_group", "group_name": name})

    def join_group(self, name: str) -> None:
        if not name.startswith("#"): name = "#" + name
        if self.running and self.sock: send_json(self.sock, {"action": "join_group", "group_name": name})

    def send_message(self, recipient: str, text: str) -> None:
        if self.running and text and self.sock and self.crypto:
            encrypted = self.crypto.encrypt_message(text)
            send_json(self.sock, {"action": "msg", "to": recipient, "text": encrypted})

    def listen(self) -> None:
        while self.running and self.sock:
            data = receive_json(self.sock)
            if not data: break
            
            action = data.get("action")
            if action == "msg":
                if self.crypto:
                    data["text"] = self.crypto.decrypt_message(data.get("text"))
                    self.on_msg(data)
            elif action == "contacts_update":
                self.on_contacts(data.get("friends", []), data.get("groups", []), data.get("requests", []))
        
        self.running = False
        if self.sock: self.sock.close()