import unittest
from cryptography.fernet import Fernet
from src.common.crypto_utils import CryptoManager

class TestCrypto(unittest.TestCase):
    def setUp(self) -> None:
        self.crypto: CryptoManager = CryptoManager()

    def test_initialization_with_key(self) -> None:
        """Test initializing with a provided key."""
        key: bytes = Fernet.generate_key()
        manager: CryptoManager = CryptoManager(key)
        self.assertEqual(manager.key, key)

    def test_initialization_without_key(self) -> None:
        """Test initializing without a key generates one."""
        manager: CryptoManager = CryptoManager()
        self.assertIsInstance(manager.key, bytes)
        self.assertTrue(len(manager.key) > 0)

    def test_get_key_as_string(self) -> None:
        """Test converting key to string."""
        key_str: str = self.crypto.get_key_as_string()
        self.assertIsInstance(key_str, str)
        # Should be decodable back to bytes
        self.assertEqual(key_str.encode('utf-8'), self.crypto.key)

    def test_encrypt_decrypt_flow(self) -> None:
        """Test valid encryption and decryption."""
        original_text: str = "Секретно съобщение 123"
        encrypted: str = self.crypto.encrypt_message(original_text)
        
        self.assertNotEqual(original_text, encrypted)
        self.assertIsInstance(encrypted, str)
        
        decrypted: str = self.crypto.decrypt_message(encrypted)
        self.assertEqual(original_text, decrypted)

    def test_encrypt_empty_message(self) -> None:
        """Test encrypting an empty string."""
        res: str = self.crypto.encrypt_message("")
        self.assertEqual(res, "")

    def test_decrypt_empty_token(self) -> None:
        """Test decrypting an empty token."""
        res: str = self.crypto.decrypt_message("")
        self.assertEqual(res, "")

    def test_decrypt_invalid_token(self) -> None:
        """Test decrypting garbage data."""
        res: str = self.crypto.decrypt_message("NotValidToken")
        self.assertEqual(res, "[Грешка при декриптиране]")

    def test_wrong_key_decryption(self) -> None:
        """Test that different keys cannot decrypt each other's messages."""
        key1: bytes = Fernet.generate_key()
        key2: bytes = Fernet.generate_key()
        
        manager1: CryptoManager = CryptoManager(key1)
        manager2: CryptoManager = CryptoManager(key2)
        
        secret: str = "My Password"
        enc: str = manager1.encrypt_message(secret)
        
        # Manager 2 tries to decrypt
        dec: str = manager2.decrypt_message(enc)
        self.assertEqual(dec, "[Грешка при декриптиране]")

if __name__ == '__main__':
    unittest.main()