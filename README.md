# Vyre

A clean, professional Roblox alt account manager for Windows. Store any number of
accounts, switch between them instantly, and browse Roblox in a built-in Chromium
window where every account keeps its own isolated session.

## Features

- **Embedded Chromium** browser (QtWebEngine) with back / forward / reload / home
- **Isolated sessions** — each account runs in its own browser profile, so switching
  is instant and accounts never bleed into each other
- **Multiple ways to log in**
  - Paste a `.ROBLOSECURITY` cookie
  - Sign in through a secure in-app Roblox login window (session captured for you)
  - Enter a username & password — Vyre fills the login form, you solve any puzzle
  - **Bulk import** many cookies, or a list of `username:password` lines at once
- **Encrypted vault** — a master password (PBKDF2 + Fernet) encrypts everything on
  disk; cookies are never stored in plain text
- **Compact, windowed UI** with search, per-account colors, and one-click switching

## Requirements

- Windows
- Python 3.10+ (tested on 3.14)

## Setup

```bash
pip install -r requirements.txt
```

Generate the app icon (already included, only needed if you change it):

```bash
python build_icon.py
```

Add a desktop shortcut:

```bash
python make_shortcut.py
```

## Run

Double-click **Vyre** on your desktop, or:

```bash
python run.py
```

On first launch you set a master password. It encrypts your vault and cannot be
recovered, so keep it safe.

## Where data is stored

Everything lives under `%APPDATA%\Vyre`:

- `vault.dat` — encrypted accounts
- `profiles\` — per-account browser sessions

## Notes

Vyre stores your own account sessions locally and never sends them anywhere except
to Roblox itself. Keep your master password private — anyone with it and the vault
file can read your saved cookies.
