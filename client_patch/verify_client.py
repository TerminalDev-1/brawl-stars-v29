"""Cold-launch the installed client and require a live process and Login packet."""
import argparse
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADB = ROOT / "tools/platform-tools/adb.exe"
PACKAGE = "com.brawlv29.client"


def adb(*args, check=True):
    return subprocess.run([str(ADB), *args], check=check, capture_output=True,
                          text=True, encoding="utf-8", errors="replace").stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=20)
    parser.add_argument("--launches", type=int, default=1)
    parser.add_argument("--require-home", action="store_true",
                        help="also require LoginOk and home data from the Python server")
    args = parser.parse_args()
    if args.seconds < 5 or args.launches < 1:
        parser.error("require --seconds >= 5 and --launches >= 1")
    for launch in range(args.launches):
        adb("shell", "am", "force-stop", PACKAGE)
        adb("shell", "am", "start", "-n", PACKAGE + "/com.supercell.brawlstars.GameApp")
        time.sleep(1)
        pid = adb("shell", "pidof", PACKAGE, check=False)
        if not pid:
            raise RuntimeError("Client died during startup")
        print("Launch", launch + 1, "PID", pid, flush=True)
        deadline = time.monotonic() + args.seconds
        next_update = time.monotonic() + 20
        while time.monotonic() < deadline:
            time.sleep(1)
            if adb("shell", "pidof", PACKAGE, check=False) != pid:
                raise RuntimeError("Client exited or restarted: PID " + pid)
            if time.monotonic() >= next_update:
                print("Still running", pid, flush=True)
                next_update += 20
        logs = adb("logcat", "-d", "-v", "threadtime", "--pid=" + pid,
                   "v29:V", "libc:F", "*:S")
        path = ROOT / "build" / ("verified-client-" + pid + ".txt")
        path.write_text(logs, encoding="utf-8")
        print(logs, flush=True)
        if "sent 10101 len" not in logs or "Fatal signal" in logs:
            raise RuntimeError("Expected Login packet without a native crash; see " + str(path))
        if args.require_home and not all(text in logs for text in ['received 20104 len', 'received 24101 len']):
            raise RuntimeError('Client did not receive LoginOk and home data; see ' + str(path))
        print("PASS:", args.seconds, "seconds alive, Login sent;", path, flush=True)


if __name__ == "__main__":
    main()
