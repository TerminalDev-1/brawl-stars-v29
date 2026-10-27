# Working agreement

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
