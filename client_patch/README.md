# v29 client

Build and install the working client while the tablet is connected over ADB:

```powershell
python client_patch/build.py --install
```

The default uses the matched `libg.so` and `lib39285EFA.so` from
`reference/priv/`, verifies their fingerprints, and loads the companion after
the game library. Omitting that companion initialization caused startup crashes.
The messaging script uses the offsets for this library pair. The original
libraries remain in `stock32/`; `--client-libraries stock` is experimental and
still has the original startup failure.

The default endpoint is `127.0.0.1:9339`. Installation also runs
`adb reverse tcp:9339 tcp:9339`, forwarding the tablet's loopback connection to
the PC server. After an ADB reconnect, repeat that reverse command. For a LAN
connection, build with `--host YOUR_PC_LAN_IP` (and optionally `--port PORT`).

```powershell
python server/test_server.py
python client_patch/verify_client.py --seconds 20 --launches 3
```

The server implements LoginOk, home data, persistent accounts, and keepalive.
Its SQLite database, JSON recovery snapshot, and debuglog.txt remain local.

For live debugging, build with `--debugger --install`, then use the bundled
Frida environment:

```powershell
tools/venv/Scripts/python.exe client_patch/debug_client.py client_patch/script.js
```

`--diagnostics` instead embeds the diagnostic script without messaging hooks.
Rebuild without those flags to restore ordinary startup. Logs use Android tags
`v29` and `v29-diagnostic`; `capture_crash.py` saves logs for an individual launch.

Required local inputs: the prepared `client_src/` apktool tree, the matching
libraries in `reference/priv/`, Java, and the existing tools in `tools/`.
Third-party binaries and generated APKs stay outside Git.
