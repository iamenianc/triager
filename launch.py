#!/usr/bin/env python3
"""launch.py - double-click launcher for the defect triage scorer.

Interactive loop: paste a defect report, finish with an empty line, get the
1-5 band and the probe readings. Starts the Ollaya server with `von` if it is
not already up. Scoring comes from von-triage.py itself (loaded at runtime),
so the launcher can never drift from production cuts/floors.

Run via launch.bat (double-click); or: python launch.py
"""
import importlib.util, json, os, subprocess, sys, time, urllib.error, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("von_triage", os.path.join(BASE, "von-triage.py"))
vt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vt)

TAGS = "http://localhost:11435/api/tags"
OLLAYA_CANDIDATES = ["ollaya", os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollaya\bin\ollaya.exe")]


def von_ready():
    try:
        with urllib.request.urlopen(TAGS, timeout=3) as r:
            return any(m.get("name", "").startswith("von") for m in json.load(r).get("models", []))
    except Exception:
        return False


def ensure_server():
    if von_ready():
        return True
    print("Ollaya/von not running - starting it (cold model load can take ~30s)...")
    for exe in OLLAYA_CANDIDATES:
        try:
            flags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
            subprocess.Popen([exe, "run", "von"], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, creationflags=flags)
            break
        except Exception:
            continue
    deadline = time.time() + 90
    while time.time() < deadline:
        if von_ready():
            print("Server is up.")
            return True
        time.sleep(2)
    print("Could not reach the Ollaya server with von loaded.")
    print("Start it manually:  ollaya run von")
    return False


def read_report():
    """Returns the pasted text, or None to quit."""
    print("\nPaste the defect report, then press Enter on an empty line.")
    print("(type q alone and press Enter to quit)")
    lines = []
    while True:
        try:
            ln = input("> " if not lines else "... ")
        except EOFError:
            return None if not lines else "\n".join(lines)
        s = ln.strip()
        if not lines and s.lower() == "q":
            return None
        if not s:
            if lines:
                return "\n".join(lines)
            continue
        lines.append(s)


def show_score(text):
    try:
        band, perq, total = vt.score(text)
    except urllib.error.URLError:
        print("Lost contact with the Ollaya server - is it still running? (ollaya run von)")
        return
    print("\n  triage score    %d/5   [defect report, sum of %d probes: %.2f/%d]"
          % (band, len(vt.PROBES), total, len(vt.PROBES)))
    for k in vt.PROBES:
        print("    %.2f  %s" % (perq[k], k))
    print()


def main():
    try:
        sys.stdin.reconfigure(errors="replace")
    except Exception:
        pass
    print("=" * 62)
    print("  von-triage - defect severity scorer (1-5)")
    print("=" * 62)
    if not ensure_server():
        try:
            input("\nPress Enter to close...")
        except EOFError:
            pass
        return
    while True:
        text = read_report()
        if text is None:
            break
        show_score(text)
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
