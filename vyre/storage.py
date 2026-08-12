import json
import os
import shutil
from typing import List, Optional

from .crypto import Cipher, VaultError, generate_salt
from .models import Account
from .paths import PROFILES_DIR, VAULT_FILE

_MAGIC = b"VYRE1"


class Vault:
    def __init__(self, cipher: Cipher, salt: bytes):
        self._cipher = cipher
        self._salt = salt
        self.accounts: List[Account] = []

    @staticmethod
    def exists() -> bool:
        return VAULT_FILE.exists()

    @classmethod
    def create(cls, password: str) -> "Vault":
        if not password:
            raise VaultError("Master password cannot be empty.")
        salt = generate_salt()
        cipher = Cipher.from_password(password, salt)
        vault = cls(cipher, salt)
        vault.save()
        return vault

    @classmethod
    def unlock(cls, password: str) -> "Vault":
        with open(VAULT_FILE, "rb") as handle:
            raw = handle.read()
        if not raw.startswith(_MAGIC):
            raise VaultError("Vault file is corrupted or unrecognized.")
        body = raw[len(_MAGIC):]
        salt, token = body[:16], body[16:]
        cipher = Cipher.from_password(password, salt)
        payload = cipher.decrypt(token)
        data = json.loads(payload.decode("utf-8"))
        vault = cls(cipher, salt)
        vault.accounts = [Account.from_dict(item) for item in data.get("accounts", [])]
        return vault

    def save(self) -> None:
        payload = {
            "accounts": [account.to_dict() for account in self.accounts],
        }
        raw = json.dumps(payload).encode("utf-8")
        token = self._cipher.encrypt(raw)
        temp = VAULT_FILE.with_suffix(".tmp")
        with open(temp, "wb") as handle:
            handle.write(_MAGIC + self._salt + token)
        os.replace(temp, VAULT_FILE)

    def add(self, account: Account) -> None:
        self.accounts.append(account)
        self.save()

    def update(self, account: Account) -> None:
        for index, existing in enumerate(self.accounts):
            if existing.id == account.id:
                self.accounts[index] = account
                break
        self.save()

    def remove(self, account_id: str) -> None:
        self.accounts = [item for item in self.accounts if item.id != account_id]
        self.save()
        profile = PROFILES_DIR / account_id
        if profile.exists():
            shutil.rmtree(profile, ignore_errors=True)

    def get(self, account_id: str) -> Optional[Account]:
        for account in self.accounts:
            if account.id == account_id:
                return account
        return None
