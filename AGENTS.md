# Working agreement

- This is a private server, not an unofficial hobby project or a public
  release. Describe it that way in README.md and elsewhere.
- Continue authorized work until the requested result is implemented and verified.
  Do not finish early after gathering evidence, writing a plan, or making a
  partial implementation. The user explicitly dislikes early stopping.
- Test client/server changes on the connected tablet when ADB is available.
  Logging a Login packet alone does not prove the user can enter the home screen.
- Preserve player data and existing user edits. Keep live databases, JSON
  backups, debug logs, credentials, signing keys, and device-specific data out
  of published source and release artifacts.
- Use Python SQLite for persistent player storage and maintain a JSON backup.
  Record each client login and protocol diagnostics in debuglog.txt without
  recording account tokens or other secrets.
- Keep the default client and native-library profiles matched. Build with the
  reference pair and required companion initialization unless deliberately
  investigating the experimental stock profile.
- Carry existing authorization forward. Ask only for information or access
  actually needed to complete the requested work; continue independent work
  while waiting. Explain a real blocker precisely if one prevents completion.
- Work directly on main and keep it synchronized with origin/main. Do not
  create separate branches unless the user explicitly requests one.
- Treat the user's instruction to "commit" as "commit and push". Commit the
  authorized changes and push main to origin; report any push failure clearly.
- Update PROJECT_STATUS.MD every time a new change is verified to work or be
  usable. Record the resulting behavior, verification evidence, and remaining
  limitations before committing and pushing the change. Keep this file current
  and distinguish verified functionality from unfinished or unverified work.
- Follow PROJECT_RULES.md. Every change is committed and pushed, and every
  change that requires a new APK ends with a published GitHub release of the
  rebuilt, tablet-verified build.
