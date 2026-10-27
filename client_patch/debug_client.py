"""Live Frida debugger for an APK built with build.py --debugger."""
import argparse
import subprocess
import time
from pathlib import Path

import frida

ROOT = Path(__file__).resolve().parent.parent
ADB = ROOT / "tools/platform-tools/adb.exe"
PACKAGE = "com.brawlv29.client"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("--seconds", type=float, default=15)
    parser.add_argument("--client-libraries", choices=["stock", "reference"], default="reference")
    args = parser.parse_args()
    subprocess.run([str(ADB), "shell", "am", "force-stop", PACKAGE], check=True)
    subprocess.run([str(ADB), "forward", "tcp:27042", "tcp:27042"], check=True)
    subprocess.run([str(ADB), "shell", "am", "start", "-n",
                    PACKAGE + "/com.supercell.brawlstars.GameApp"], check=True)
    device = None
    processes = []
    for _ in range(50):
        try:
            device = frida.get_device_manager().add_remote_device("127.0.0.1:27042")
            processes = device.enumerate_processes()
            if processes:
                break
        except (frida.TransportError, frida.ServerNotRunningError):
            time.sleep(0.2)
    if device is None or not processes:
        raise RuntimeError("Gadget did not become reachable")
    process = next((p for p in processes if p.name == "Gadget"), processes[0])
    print("Attaching", process, flush=True)
    session = device.attach(process.pid)
    session.on("detached", lambda *info: print("DETACHED", info, flush=True))
    import json
    script = session.create_script('globalThis.V29_LIBRARY_PROFILE = ' +
                                   json.dumps(args.client_libraries) + ';\n' +
                                   args.script.read_text(encoding="utf-8"))
    script.on("message", lambda message, data: print(message, flush=True))
    script.load()
    device.resume(process.pid)
    time.sleep(args.seconds)
    try:
        session.detach()
    except (frida.TransportError, frida.InvalidOperationError):
        pass


if __name__ == "__main__":
    main()
