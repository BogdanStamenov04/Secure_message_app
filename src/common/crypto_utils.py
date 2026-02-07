"""
Utility module for cryptographic operations using Fernet (symmetric encryption).
Handles key generation, storage, and message encryption/decryption.
"""

import os
from typing import Optional
from cryptography.fernet import Fernet

KEY_FILE: str = "server.key"


class CryptoManager:
    """
    Manages symmetric encryption using Fernet (AES).
    Handles key generation, persistence, encryption, and decryption.
    """

    def __init__(self, key: Optional[bytes] = None) -> None:
        """
        Initializes the CryptoManager.

        Args:
            key: Optional key bytes. If provided (Client), it uses it.
                 If None (Server), it loads from file or generates a new one.
        """
        self.key: bytes

        if key:
            self.key = key
        else:
            self.key = self._load_or_generate_key()

        self.cipher: Fernet = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        """
        Checks for an existing key file. Loads it if present,
        otherwise generates a new key and saves it.
        """
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                return f.read()

        new_key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(new_key)
        return new_key

    def get_key_as_string(self) -> str:
        """Returns the key as a string for network transmission."""
        return self.key.decode('utf-8')

    def encrypt_message(self, message: str) -> str:
        """Encrypts a plaintext string into a Fernet token."""
        if not message:
            return ""
        try:
            return self.cipher.encrypt(message.encode('utf-8')).decode('utf-8')
        except Exception:  # pylint: disable=broad-exception-caught
            return ""

    def decrypt_message(self, encrypted_token: str) -> str:
        """Decrypts a Fernet token back to plaintext."""
        if not encrypted_token:
            return ""
        try:
            return self.cipher.decrypt(encrypted_token.encode('utf-8')).decode('utf-8')
        except Exception:  # pylint: disable=broad-exception-caught
            return "[Decryption Error]"
