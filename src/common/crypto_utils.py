from cryptography.fernet import Fernet
from typing import Optional

class CryptoManager:
    def __init__(self, key: Optional[bytes] = None) -> None:
        # Ако няма ключ (Server), генерира нов.
        # Ако има ключ (Client), ползва него.
        self.key: bytes = key if key else Fernet.generate_key()
        self.cipher: Fernet = Fernet(self.key)

    def get_key_as_string(self) -> str:
        """Връща ключа като стринг за изпращане по мрежата."""
        return self.key.decode('utf-8')

    def encrypt_message(self, message: str) -> str:
        if not message: return ""
        try:
            return self.cipher.encrypt(message.encode('utf-8')).decode('utf-8')
        except Exception:
            return ""

    def decrypt_message(self, encrypted_token: str) -> str:
        if not encrypted_token: return ""
        try:
            return self.cipher.decrypt(encrypted_token.encode('utf-8')).decode('utf-8')
        except Exception:
            return "[Грешка при декриптиране]"