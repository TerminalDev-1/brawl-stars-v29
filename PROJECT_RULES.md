# Project rules

These rules are mandatory for every change to this project. They are not
optional and must not be skipped.

## Commit and push every change

- Commit every finished change with a clear message and push `main` to
  `origin` before ending the turn.
- Commit only the files that belong to the change.

## Publish a new build whenever the APK changes

- Any change that requires a new APK (anything under `client_patch/`, game-data
  edits in `client_patch/balance.py`, client libraries, or `client_src/`) must
  end with a published GitHub release of the rebuilt APK. Server-only changes
  do not need a new release.
- Before publishing:
  1. Rebuild with `python client_patch/build.py`.
  2. Install it on the tablet and verify the change there.
  3. Confirm the build is byte-identical to the APK installed on the tablet.
- Publish the release:
  1. Tag it on the pushed commit that produced the build, using the next
     version number (v0.3.1, v0.3.2, ... for small changes; v0.4.0 for larger
     feature sets).
  2. Attach `brawl_v29.apk` and `SHA256SUMS.txt` (`<sha256>  brawl_v29.apk`).
  3. Write release notes listing what changed, the update steps and what was
     verified.
- After publishing, confirm the release is public, not a draft, and that
  GitHub's asset digest matches the local APK.
- Record the new release, its commit and the APK SHA256 in
  `PROJECT_STATUS.MD`, then commit and push that update.
