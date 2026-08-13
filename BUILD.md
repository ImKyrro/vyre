# Building Vyre as a standalone app

Vyre ships as Python, but you can compile it to a single native `Vyre.exe` that
runs without Python installed and is hard to reverse engineer.

## Recommended: Nuitka (compiled, hardest to reverse)

Nuitka compiles Python to C and then to real machine code, so there is no
readable source or `.pyc` bytecode inside the exe to extract.

```bash
pip install nuitka
python build_exe.py
```

Output: `build_out/Vyre.exe` (one file, no console). First run may be slightly
slower while it unpacks. The build itself can take 15-40 minutes and will
download a C compiler the first time.

## Reverse engineering — the honest truth

No application, in any language, is 100% impossible to reverse engineer. What you
can do is raise the cost:

- **Nuitka** (used above) is far stronger than PyInstaller. PyInstaller exes can
  be unpacked and decompiled back to near-original source; Nuitka output is
  compiled machine code with no bundled bytecode.
- Your **secrets stay encrypted** regardless: the vault uses your master password,
  so even with the code, saved cookies can't be read without it.
- For more, a commercial protector/obfuscator or a licensing service can be layered
  on top, but that is diminishing returns for most projects.

## Antivirus false positives

Freshly built, unsigned exes are sometimes flagged by SmartScreen/AV. This is about
**reputation**, not your code. To reduce or remove it:

1. **Code-sign the exe.** This is the only real fix. A standard or (best) EV
   code-signing certificate from a CA makes Windows trust the publisher. Sign with:
   ```bash
   signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 build_out/Vyre.exe
   ```
2. This build already sets product/version/company metadata, which helps.
3. It does **not** use UPX compression (UPX is a common false-positive trigger).
4. If flagged, submit the exe to Microsoft for analysis:
   https://www.microsoft.com/wdsi/filesubmission — reputation builds after a few
   downloads and a submission.

Without a certificate, expect a one-time SmartScreen "More info -> Run anyway" until
reputation builds. A cert removes that.
