# django/app/keys/crypto.py 
"""
AES-128-CBC 暗号化/復号化ユーティリティ
TG Octopus Energy スマートメーター仕様書 Section 3.15 準拠
"""
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import logging

logger = logging.getLogger(__name__)

# 固定IV（仕様書より、変更不可）
INITIAL_VECTOR = b'420#abA%,ZfE79@M'
DEFAULT_KEY = '69aF7&3KY0_kk89@'


def encrypt_data(plaintext: bytes, key: str) -> bytes:
    """
    AES-128-CBC で暗号化
    
    Args:
        plaintext: 平文データ（bytes）
        key: 暗号鍵（16文字ASCII）
    
    Returns:
        暗号化データ（bytes）
    """
    key_bytes = key.encode('ascii') if isinstance(key, str) else key
    
    if len(key_bytes) != 16:
        raise ValueError(f'Key must be 16 bytes, got {len(key_bytes)}')
    
    cipher = AES.new(key_bytes, AES.MODE_CBC, INITIAL_VECTOR)
    padded = pad(plaintext, AES.block_size)
    return cipher.encrypt(padded)


def decrypt_data(ciphertext: bytes, key: str) -> bytes:
    """
    AES-128-CBC で復号
    
    Args:
        ciphertext: 暗号化データ（bytes）
        key: 暗号鍵（16文字ASCII）
    
    Returns:
        平文データ（bytes）
    """
    key_bytes = key.encode('ascii') if isinstance(key, str) else key
    
    if len(key_bytes) != 16:
        raise ValueError(f'Key must be 16 bytes, got {len(key_bytes)}')
    
    cipher = AES.new(key_bytes, AES.MODE_CBC, INITIAL_VECTOR)
    decrypted = cipher.decrypt(ciphertext)
    return unpad(decrypted, AES.block_size)


def encrypt_hex(plaintext_hex: str, key: str) -> str:
    """
    HEX文字列を暗号化してHEX文字列で返す
    
    Args:
        plaintext_hex: 平文HEX文字列
        key: 暗号鍵
    
    Returns:
        暗号化HEX文字列
    """
    plaintext = bytes.fromhex(plaintext_hex)
    encrypted = encrypt_data(plaintext, key)
    return encrypted.hex().upper()


def decrypt_hex(ciphertext_hex: str, key: str) -> str:
    """
    HEX文字列を復号してHEX文字列で返す
    
    Args:
        ciphertext_hex: 暗号化HEX文字列
        key: 暗号鍵
    
    Returns:
        平文HEX文字列
    """
    ciphertext = bytes.fromhex(ciphertext_hex)
    decrypted = decrypt_data(ciphertext, key)
    return decrypted.hex().upper()


def try_decrypt(ciphertext_hex: str, keys: list) -> tuple:
    """
    複数の鍵で復号を試みる
    
    Args:
        ciphertext_hex: 暗号化HEX文字列
        keys: 試す鍵のリスト [('key_name', 'key_value'), ...]
    
    Returns:
        (平文HEX, 使用した鍵名) or (None, None)
    """
    for key_name, key_value in keys:
        try:
            decrypted = decrypt_hex(ciphertext_hex, key_value)
            logger.debug(f'Decryption succeeded with {key_name}')
            return decrypted, key_name
        except Exception as e:
            logger.debug(f'Decryption failed with {key_name}: {e}')
            continue
    return None, None