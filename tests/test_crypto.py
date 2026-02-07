import os
import base64
from unittest.mock import patch, mock_open
from cryptography.fernet import Fernet
from src.common.crypto_utils import CryptoManager, KEY_FILE


def test_init_with_provided_key():
    """Test initializing with an explicit key (Client mode)."""
    # FIX: Генерираме валиден Fernet ключ
    valid_key = Fernet.generate_key()
    manager = CryptoManager(key=valid_key)
    assert manager.key == valid_key


@patch('os.path.exists')
def test_init_server_existing_key(mock_exists):
    """Test loading existing key from file (Server mode)."""
    mock_exists.return_value = True

    # FIX: Създаваме валиден ключ и го "слагаме" във файла
    valid_key = Fernet.generate_key()

    with patch('builtins.open', mock_open(read_data=valid_key)) as mock_file:
        manager = CryptoManager()

        assert manager.key == valid_key
        mock_file.assert_called_with(KEY_FILE, "rb")


@patch('os.path.exists')
def test_init_server_generate_key(mock_exists):
    """Test generating new key if file doesn't exist."""
    mock_exists.return_value = False

    with patch('builtins.open', mock_open()) as mock_file:
        manager = CryptoManager()

        assert len(manager.key) > 0
        # Проверяваме дали е записал нещо във файла
        mock_file.assert_called_with(KEY_FILE, "wb")
        handle = mock_file()
        handle.write.assert_called_once()


def test_get_key_as_string():
    valid_key = Fernet.generate_key()
    manager = CryptoManager(key=valid_key)
    assert manager.get_key_as_string() == valid_key.decode('utf-8')


def test_encrypt_decrypt_flow():
    """Test full encryption cycle."""
    manager = CryptoManager()  # Generates random valid key
    original = "Secret Message"

    encrypted = manager.encrypt_message(original)
    assert encrypted != original
    assert encrypted != ""

    decrypted = manager.decrypt_message(encrypted)
    assert decrypted == original


def test_encrypt_empty():
    manager = CryptoManager()
    assert manager.encrypt_message("") == ""
    assert manager.encrypt_message(None) == ""


def test_decrypt_empty():
    manager = CryptoManager()
    assert manager.decrypt_message("") == ""
    assert manager.decrypt_message(None) == ""


def test_decrypt_invalid():
    manager = CryptoManager()
    assert manager.decrypt_message("InvalidToken") == "[Decryption Error]"
