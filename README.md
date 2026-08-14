<div align="center">
  <img src="docs/screenshots/main.png" alt="Vyre" width="800">

  # Vyre 
  **The ultimate professional Roblox alt account manager for Windows.**

  [![Latest Release](https://img.shields.io/github/v/release/ImKyrro/vyre?label=Version&color=e5484d&style=for-the-badge)](https://github.com/ImKyrro/vyre/releases/latest)
  [![Downloads](https://img.shields.io/github/downloads/ImKyrro/vyre/total?color=2b9348&style=for-the-badge)](https://github.com/ImKyrro/vyre/releases)
  [![Platform](https://img.shields.io/badge/Platform-Windows-0078d7?style=for-the-badge&logo=windows)](https://github.com/ImKyrro/vyre/releases)

  *Manage accounts, embedded Chromium, live presence, one-click game launching, and more.*

  [**⬇ Download Latest Vyre.exe**](https://github.com/ImKyrro/vyre/releases/latest/download/Vyre.exe)
</div>

---

## 📖 Table of Contents
- [✨ Key Features](#-key-features)
- [🚀 Installation & Setup](#-installation--setup)
- [🔒 Security & Data](#-security--data)
- [🤖 MCP Server for AI](#-mcp-server-for-ai)
- [💖 Support](#-support)

---

## ✨ Key Features

### 👤 Account Management
* **Unlimited Accounts:** Store unlimited accounts with real Roblox avatars and customizable accent colors.
* **Organize:** Favorite (star), reorder, duplicate, and search accounts instantly.
* **Rich Profiles:** View Display Names, User IDs, and live Friends/Followers/Following statistics.

### 🔑 Secure Login Methods
* **Cookie Login:** Paste your `.ROBLOSECURITY` cookie directly.
* **In-App Login:** Sign in through a secure embedded Roblox window—your session is captured automatically.
* **Auto-Fill:** Enter username & password and Vyre handles the rest.
* **Bulk Import:** Import massive lists of cookies or `username:password` combinations at once.

### 🌐 Embedded Chromium Browser
* **Isolated Profiles:** Every account runs in its own isolated browser profile via QtWebEngine.
* **Full Navigation:** Includes back, forward, reload, home, and open-external actions.
* **Quick Access:** Open any account's profile or settings page in-app with a single click.

### 🟢 Live Presence & Tracking
* **Real-time Status:** Instantly see if accounts are Online, In-Game, In Studio, or Offline.
* **Server Tracking:** See exactly which game an account is playing and jump straight into their server.

### 🎮 Game Launching
* **One-Click Launch:** Launch any game by Place ID or saved link.
* **VIP & Private Servers:** Save multiple VIP servers per account with auto-fetched game icons. Join by link or access code.
* **Mass-Launch:** Select multiple accounts and launch them all into a game with configurable stagger intervals.
* **Server Browser:** Browse active game servers with live player counts directly in the app.

### 🛠️ Roblox Window Tools
* **Multi-Instance:** Allow multiple Roblox clients to run simultaneously (bypasses singleton locks).
* **Window Management:** Minimize all, restore all, or neatly tile every open Roblox client into a grid.
* **Resource Management:** Lower the CPU/GPU priority of background accounts to free up system resources.

---

## 🚀 Installation & Setup

### For Regular Users
No installation required! Vyre is a standalone portable executable.
1. Download `Vyre.exe` from the [Releases Page](https://github.com/ImKyrro/vyre/releases/latest).
2. Double-click to run. 
*(Note: Windows SmartScreen may show a prompt on the first run since the build isn't code-signed yet. Click **More info → Run anyway**).*
3. On first launch, you will be prompted to create a **Master Password**. This encrypts your vault. **Keep it safe!**

### For Developers
If you want to run Vyre from source:
```bash
pip install -r requirements.txt
python run.py
```
*(Optional) Create a desktop shortcut:* `python make_shortcut.py`

---

## 🔒 Security & Data
Vyre takes your privacy seriously. Your data is stored locally and encrypted:
* **Encryption:** The vault is encrypted using **PBKDF2 + Fernet** with your Master Password. Cookies are never saved in plaintext.
* **Local Storage:** Everything is stored locally in `%APPDATA%\Vyre` (including `vault.dat`, `config.json`, and isolated browser `profiles\`).
* **Direct Connections:** Vyre only communicates directly with Roblox servers.

---

## 🤖 MCP Server for AI
Vyre ships with a built-in **Model Context Protocol (MCP)** server, allowing AI agents to interact with your Roblox accounts.
* **Command:** `python -m vyre.mcp_server`
* **Features:** Read accounts, check presence, fetch game info, and launch games directly from AI prompts.
* **Setup:** Requires the `VYRE_MASTER_PASSWORD` environment variable. You can copy a ready-made client config from **Settings → MCP** in the app.

---

## 💖 Support
Vyre is developed and maintained by **Kyrro**. If this tool helps you, consider supporting its development!

* **Discord:** `kyrro_real`
* **Litecoin (LTC):** `LSmU3RodML3p2HvwN2wU4HUJZSJddMxUJW`

*(Open the ♥ Support tab in the app to copy these links quickly).*
