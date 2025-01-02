from cryptography.fernet import Fernet
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get or generate encryption key
def get_encryption_key():
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        # Generate a new key if none exists
        key = Fernet.generate_key()
        # In production, you would want to save this key securely
        print("WARNING: No encryption key found in environment. Generated new key:", key.decode())
    return key if isinstance(key, bytes) else key.encode()

# Initialize Fernet cipher with the encryption key
cipher_suite = Fernet(get_encryption_key())

def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key and return the encrypted value as a base64 string"""
    if not api_key:
        return None
    encrypted_bytes = cipher_suite.encrypt(api_key.encode())
    return base64.b64encode(encrypted_bytes).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an encrypted API key from its base64 string representation"""
    if not encrypted_key:
        return None
    try:
        encrypted_bytes = base64.b64decode(encrypted_key)
        decrypted_bytes = cipher_suite.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
    except Exception as e:
        print(f"Error decrypting API key: {str(e)}")
        return None
