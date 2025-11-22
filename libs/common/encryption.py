"""
AES-256 encryption for PII data
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os
from dotenv import load_dotenv

load_dotenv()

class Encryptor:
    """AES-256 encryption/decryption for sensitive data"""
    
    def __init__(self):
        # Get encryption key from environment
        key_string = os.getenv("ENCRYPTION_KEY")
        if not key_string:
            raise ValueError("ENCRYPTION_KEY not set in environment")
        
        # Derive Fernet key from the encryption key
        self.fernet = Fernet(key_string.encode())
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string
        
        Args:
            plaintext: String to encrypt (e.g., NIK, NPWP)
        
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self.fernet.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted_bytes).decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string
        
        Args:
            ciphertext: Base64-encoded encrypted string
        
        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""
        
        encrypted_bytes = base64.b64decode(ciphertext.encode('utf-8'))
        decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')


# Singleton instance
_encryptor = None

def get_encryptor() -> Encryptor:
    """Get singleton encryptor instance"""
    global _encryptor
    if _encryptor is None:
        _encryptor = Encryptor() 
    return _encryptor


def encrypt_pii(value: str) -> str:
    """Convenience function to encrypt PII"""
    return get_encryptor().encrypt(value)


def decrypt_pii(value: str) -> str:
    """Convenience function to decrypt PII"""
    return get_encryptor().decrypt(value)


# Example usage:
# encrypted_nik = encrypt_pii("3273010101990001")
# decrypted_nik = decrypt_pii(encrypted_nik)
