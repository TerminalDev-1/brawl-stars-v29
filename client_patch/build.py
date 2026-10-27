"""Build, sign and (optionally) install the patched v29 client.

Usage:
    python client_patch/build.py            # build + sign
    python client_patch/build.py --install  # build + sign + install over adb

Expects:
    client_src/  - the 32-bit 29.270 APK unpacked with apktool, already patched
                   (package renamed, GameApp loads "gadget" before "g")
    tools/       - apktool.jar, uber-apk-signer.jar, libfrida-gadget-arm.so, platform-tools/
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "client_src"
PATCH = ROOT / "client_patch"
TOOLS = ROOT / "tools"
OUT = ROOT / "build"
LIB = SRC / "lib" / "armeabi-v7a"
PACKAGE = "com.brawlv29.client"
LIBRARY_HASHES = {
    "stock": {"libg.so": "7e9a6356006e288a7d345a18166dd1b89256901f",
              "lib39285EFA.so": "04142fe64b06a8bf4ea0e43820d2654a22a82053"},
    "reference": {"libg.so": "5346db9d6258e7bf68034a18d45e37f40e047ee6",
                  "lib39285EFA.so": "45fc3fe74224a9e2877163578b66ceb6e087a03e"},
}


def run(*cmd):
    print(">", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--diagnostics", action="store_true",
                        help="capture native crash evidence without messaging hooks")
    parser.add_argument("--debugger", action="store_true",
                        help="wait for a Frida debugger through an ADB port forward")
    parser.add_argument("--client-libraries", choices=["stock", "reference"], default="reference",
                        help="matched native library pair (stock remains experimental)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9339)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    libraries = ROOT / ("stock32" if args.client_libraries == "stock" else "reference/priv")
    for name in ("libg.so", "lib39285EFA.so"):
        if hashlib.sha1((libraries / name).read_bytes()).hexdigest() != LIBRARY_HASHES[args.client_libraries][name]:
            raise RuntimeError("Unexpected library revision: " + str(libraries / name))
        shutil.copyfile(libraries / name, LIB / name)

    # The reference companion initializes its matching game library after load.
    # Keeping the .so in the APK alone does not run that initialization.
    startup = SRC / "smali/com/supercell/titan/GameApp.smali"
    original_source = source = startup.read_text(encoding="utf-8")
    marker = '    .line 5882\n    iput-boolean v14, v15, Lcom/supercell/titan/GameApp;->p:Z'
    helper_load = ('    const-string v0, "39285EFA"\n\n'
                   '    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V\n\n')
    source = source.replace(helper_load, "")
    if args.client_libraries == "reference":
        if source.count(marker) != 1:
            raise RuntimeError("Cannot locate GameApp library initialization")
        source = source.replace(marker, helper_load + marker)
    if source != original_source:
        startup.write_text(source, encoding="utf-8")

    # Gadget + its config + our script, all shipped as native libs so they get extracted.
    shutil.copyfile(TOOLS / "libfrida-gadget-arm.so", LIB / "libgadget.so")
    shutil.copyfile(PATCH / "gadget.config.json", LIB / "libgadget.config.so")
    if args.debugger:
        (LIB / "libgadget.config.so").write_text(json.dumps({"interaction": {
            "type": "listen", "address": "127.0.0.1", "port": 27042,
            "on_load": "wait"}}), encoding="utf-8")
    script = "diagnostics.js" if args.diagnostics else "script.js"
    settings = ('globalThis.V29_LIBRARY_PROFILE = ' + json.dumps(args.client_libraries) + ';\n'
                'globalThis.V29_SERVER_CONFIG = ' + json.dumps({"host": args.host, "port": args.port}) + ';\n')
    (LIB / "libgadget.script.so").write_text(
        settings + (PATCH / script).read_text(encoding="utf-8"), encoding="utf-8")

    OUT.mkdir(exist_ok=True)
    unsigned = OUT / "brawl_v29_unsigned.apk"
    run("java", "-jar", TOOLS / "apktool.jar", "b", SRC, "-o", unsigned)
    signed_dir = OUT / "signed"
    shutil.rmtree(signed_dir, ignore_errors=True)
    run("java", "-jar", TOOLS / "uber-apk-signer.jar", "-a", unsigned, "-o", signed_dir, "--allowResign")

    signed = next(signed_dir.glob("*.apk"))
    final = OUT / "brawl_v29.apk"
    shutil.move(signed, final)
    shutil.rmtree(signed_dir, ignore_errors=True)
    print("built", final)

    if args.install:
        adb = TOOLS / "platform-tools" / "adb.exe"
        run(adb, "install", "-r", "--abi", "armeabi-v7a", final)
        if args.host == "127.0.0.1":
            run(adb, "reverse", "tcp:" + str(args.port), "tcp:" + str(args.port))
        print("installed", PACKAGE)


if __name__ == "__main__":
    main()
