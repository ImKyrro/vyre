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

    def move(self, account_id: str, delta: int) -> None:
        index = next((i for i, a in enumerate(self.accounts) if a.id == account_id), None)
        if index is None:
            return
        target = max(0, min(len(self.accounts) - 1, index + delta))
        if target == index:
            return
        self.accounts.insert(target, self.accounts.pop(index))
        self.save()

    def sorted_accounts(self) -> List[Account]:
        return sorted(self.accounts, key=lambda a: (not a.favorite,))

    def set_order(self, ordered_ids: List[str]) -> None:
        rank = {account_id: index for index, account_id in enumerate(ordered_ids)}
        self.accounts.sort(key=lambda a: rank.get(a.id, len(rank)))
        self.save()

    def change_password(self, new_password: str) -> None:
        if not new_password:
            raise VaultError("Master password cannot be empty.")
        salt = generate_salt()
        self._cipher = Cipher.from_password(new_password, salt)
        self._salt = salt
        self.save()

    def export_to(self, path, password: str) -> None:
        cipher = Cipher.from_password(password, self._salt)
        payload = {"accounts": [a.to_dict() for a in self.accounts]}
        token = cipher.encrypt(json.dumps(payload).encode("utf-8"))
        with open(path, "wb") as handle:
            handle.write(_MAGIC + self._salt + token)

    def import_from(self, path, password: str) -> int:
        with open(path, "rb") as handle:
            raw = handle.read()
        if not raw.startswith(_MAGIC):
            raise VaultError("Not a valid Vyre export file.")
        body = raw[len(_MAGIC):]
        salt, token = body[:16], body[16:]
        cipher = Cipher.from_password(password, salt)
        data = json.loads(cipher.decrypt(token).decode("utf-8"))
        existing = {a.id for a in self.accounts}
        added = 0
        for item in data.get("accounts", []):
            account = Account.from_dict(item)
            if account.id in existing:
                continue
            self.accounts.append(account)
            existing.add(account.id)
            added += 1
        self.save()
        return added
