"""
Symmetric encryption for connection strings at rest, via Fernet
(AES-128-CBC + HMAC, from the `cryptography` package).

DB_ENCRYPTION_KEY must be a Fernet key (Fernet.generate_key()). Decrypted
connection strings must never be logged or returned in an API response —
callers of decrypt_connection_string() are responsible for that discipline;
this module only handles the crypto.
"""

import os

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

load_dotenv()

_key = os.getenv("DB_ENCRYPTION_KEY")


def _get_fernet() -> Fernet:
    if not _key:
        raise RuntimeError(
            "DB_ENCRYPTION_KEY is not set. Generate one with "
            "`python -c \"from cryptography.fernet import Fernet; "
            'print(Fernet.generate_key().decode())"` and add it to your .env file.'
        )
    return Fernet(_key.encode())


def encrypt_connection_string(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_connection_string(ciphertext: str) -> str:
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        # Wrong/rotated DB_ENCRYPTION_KEY, or the ciphertext was tampered with.
        raise ValueError("Stored connection string could not be decrypted.")
