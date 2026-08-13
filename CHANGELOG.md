# Changelog

## 1.1.4

- Added Quick Sign In code copy button to easily copy generated auth codes
- Fixed Chrome companion extension "Could not connect to Vyre" by implementing CORS preflight and endpoint headers
- Added local /launch_game API endpoint enabling Roblox game launching directly from companion extension
- Added rounded app window corners and border outline stylesheet rules in frameless mode
- Added TitleBar update downloading button that replaces the current app and restarts on click
- Added Private Server Link input and saving options on accounts
- Added automatic Place ID extraction from private server links in LaunchDialog
- Implemented companion extension Vault UI Quick Launch box and connected version badge
- Added detailed step-by-step MCP connection instructions inside Settings

## 1.1.3

- Fixed missing QPushButton NameError import crash on MainWindow TitleBar buttons
- Fixed positional clicked signal parameter mismatch on UnlockDialog submit

## 1.1.2

- Added Quick Sign In method to bypass captcha and bot detection entirely
- Implemented custom title bar (frameless window mode) with minimize, maximize, and close controls
- Added download speed and progress reporting to installer, with automatic old version cleanup
- Added VC++ redistributable requirements checker with automatic links in installer UI
- Bundle assets folder in standalone binaries resolving missing application and taskbar icons
- Fixed private server linkCode parsing and launch errors
- Fixed crashes on update re-checks, download updates, and what's new buttons

## 1.1.1

- Implemented Chrome extension local API capture receiver
- Randomized birthdate (month, day, year) in automated signup flow
- Added sidebar update button notifier in header
- Fixed update checking errors reporting

## 1.1.0

- Automated Roblox signup flow: autofills birthday (18+), username, and password, then submits automatically
- HWID Spoofing: randomizes Roblox client registry keys (CrashGUID, HardwareID, DeviceID, and MachineGuid) on launch to prevent hardware tracking
- Added HWID Spoofing toggle in General Settings
- Simplified account importing by directly capturing the cookie after registration

## 1.0.0

- Encrypted vault with a master password, plus multiple profiles
- Add accounts by cookie, in-app sign in, username/password, or bulk import
- Embedded Chromium browser with isolated per-account sessions
- Real avatars, live presence, favourites, drag reorder, search
- Launch games as any account: place / job / private server, server browser
- Multi-select mass launch and join a user or friend
- Multiple Roblox instances, plus window tools (grid, shrink, minimise)
- Account & email view with resend verification
- Cookie health checks, hide-info and hide-avatar privacy modes
- Debug console, update checker, and an MCP server for AI clients
