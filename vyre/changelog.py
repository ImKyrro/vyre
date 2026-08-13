TEXT = """Vyre 1.1.2
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
