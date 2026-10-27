"""Launch the local client and save bounded, process-specific Android logs."""
import argparse
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADB = ROOT / "tools" / "platform-tools" / "adb.exe"
PACKAGE = "com.brawlv29.client"


def adb(*args):
    return subprocess.run([str(ADB), *args], check=True, capture_output=True,
                          text=True, encoding="utf-8", errors="replace").stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 60:
        parser.error("--seconds must be between 1 and 60")
    # Preserve the device's existing log buffers; filter by this launch time.
    since = adb("shell", "date '+%m-%d %H:%M:%S.000'").strip()
    adb("shell", "am", "force-stop", PACKAGE)
    print(adb("shell", "am", "start", "-W", "-n",
              PACKAGE + "/com.supercell.brawlstars.GameApp").strip())
    time.sleep(args.seconds)
    output = ROOT / "build" / ("crash-" + time.strftime("%Y%m%d-%H%M%S"))
    output.mkdir(parents=True, exist_ok=False)
    recent = adb("logcat", "-d", "-v", "threadtime", "-T", since)
    # ActivityManager records the PID even when the process dies before am -W returns.
    import re
    pids = set(re.findall(r"Start proc (\d+):" + re.escape(PACKAGE), recent))
    pids.update(re.findall(r"^\S+\s+\S+\s+(\d+)\s+\d+\s+\S+\s+v29-diagnostic:",
                           recent, re.MULTILINE))
    for pid in sorted(pids):
        (output / (pid + ".txt")).write_text(
            adb("logcat", "-d", "-v", "threadtime", "-T", since, "--pid=" + pid),
            encoding="utf-8")
    (output / "native-crash.txt").write_text(
        adb("logcat", "-d", "-b", "crash", "-v", "threadtime", "-T", since),
        encoding="utf-8")
    print("Saved logs:", output, "PIDs:", ", ".join(sorted(pids)) or "not found")


if __name__ == "__main__":
    main()
