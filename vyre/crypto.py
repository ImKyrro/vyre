import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_ITERATIONS = 390000
_SALT_SIZE = 16


class VaultError(Exception):
    pass


def generate_salt() -> bytes:
    return os.urandom(_SALT_SIZE)


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


class Cipher:
    def __init__(self, key: bytes):
        self._fernet = Fernet(key)

    @classmethod
    def from_password(cls, password: str, salt: bytes) -> "Cipher":
        return cls(derive_key(password, salt))

    def encrypt(self, data: bytes) -> bytes:
        return self._fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        try:
            return self._fernet.decrypt(token)
        except InvalidToken as error:
            raise VaultError("Incorrect master password.") from error
