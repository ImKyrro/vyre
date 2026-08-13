# Publishing Vyre to a new GitHub repo

Your data never gets committed — `.gitignore` already excludes the vault, config,
profiles, logs, exports, and the built `.exe`. Only source code goes up.

## 1. Create an empty repo

On github.com, create a new repository (e.g. `vyre`). Do **not** add a README,
license, or .gitignore there (this project already has them).

## 2. Point this project at it

From the project folder:

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/vyre.git
git branch -M main
git push -u origin main
```

If `git remote remove origin` errors with "No such remote", ignore it.

## 3. Verify nothing personal was pushed

After pushing, check the repo on github.com. You should NOT see `vault.dat`,
`config.json`, `profiles.json`, or anything under `profiles/`. If you do, stop and
tell me.

## 4. (Optional) Releases + auto-update

To use Vyre's built-in update checker with GitHub:

1. Build the exe: `python build_exe.py`
2. On github.com, draft a new **Release**, tag it `v1.0.1` (bump the number),
   and attach `build_out/Vyre.exe`.
3. In Vyre → Settings → About, set the update URL to:
   `https://api.github.com/repos/YOUR_USERNAME/vyre/releases/latest`

Vyre will then notify you when a newer release tag is published.

## Notes

- The `Support` section in the README shows your Kyrro donation info on purpose. If
  you'd rather keep the repo anonymous, remove that section before pushing.
- Screenshots in `docs/screenshots/` use generic public accounts (Builderman, etc.),
  not your accounts.
