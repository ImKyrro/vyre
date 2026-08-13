TEXT = """Vyre 1.1.6
- Implemented background threading for launching Roblox via local API to prevent blocking local QHttpServer and causing extension timeouts
- Fixed console QPainter draw engine warnings by safely checking painter.begin() in paintEvents
- Added application V logo icon in the frameless custom TitleBar next to the app name

Vyre 1.1.5
- Fixed QWidget background transparency issues in frameless window mode by adding paintEvent methods to custom widget subclasses
- Added raw GitHub version checking bypass to fully resolve GitHub API rate-limiting errors

Vyre 1.1.4
- Added Quick Sign In code copy button to easily copy generated auth codes
- Fixed Chrome companion extension "Could not connect to Vyre" by implementing CORS preflight and endpoint headers
- Added local /launch_game API endpoint enabling Roblox game launching directly from companion extension
- Added rounded app window corners and border outline stylesheet rules in frameless mode
- Added TitleBar update downloading button that replaces the current app and restarts on click
- Added Private Server Link input and saving options on accounts
- Added automatic Place ID extraction from private server links in LaunchDialog
- Implemented companion extension Vault UI Quick Launch box and connected version badge
- Added detailed step-by-step MCP connection instructions inside Settings

Vyre 1.1.3
- Fixed missing QPushButton NameError import crash on MainWindow TitleBar buttons
- Fixed positional clicked signal parameter mismatch on UnlockDialog submit

Vyre 1.1.2
- Added Quick Sign In method to bypass captcha and bot detection entirely
- Implemented custom title bar (frameless window mode) with minimize, maximize, and close controls
- Added download speed and progress reporting to installer, with automatic old version cleanup
- Added VC++ redistributable requirements checker with automatic links in installer UI
- Bundle assets folder in standalone binaries resolving missing application and taskbar icons
- Fixed private server linkCode parsing and launch errors
- Fixed crashes on update re-checks, download updates, and what's new buttons

Vyre 1.1.1
- Implemented Chrome extension local API capture receiver
- Randomized birthdate (month, day, year) in automated signup flow
- Added sidebar update button notifier in header
- Fixed update checking errors reporting

Vyre 1.1.0
- Automated Roblox signup flow: autofills birthday (18+), username, and password, then submits automatically
- HWID Spoofing: randomizes Roblox client registry keys (CrashGUID, HardwareID, DeviceID, and MachineGuid) on launch to prevent hardware tracking
- Added HWID Spoofing toggle in General Settings
- Simplified account importing by directly capturing the cookie after registration
"""
