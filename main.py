# TriLingo Translator
# ===================
# Offline desktop translator supporting English, Urdu, and Sindhi
# with Text-to-Speech, translation history, and a modern GUI.
#
# Author: TriLingo Project
# License: MIT

import sys
import os

# ── Windows-safe path fix ──────────────────────────────────────────────────
# Get the absolute directory where THIS file lives (works on Windows & Linux)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add it to sys.path so all sub-packages (gui, translator, tts, data) resolve
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ── Tkinter availability check ────────────────────────────────────────────
try:
    import tkinter
except ImportError:
    print("ERROR: tkinter is not installed.")
    print("  Windows : Re-install Python and tick 'tcl/tk and IDLE' in the installer.")
    print("  Linux   : sudo apt install python3-tk")
    sys.exit(1)

# ── Launch app ────────────────────────────────────────────────────────────
from gui.app import TriLingoApp


def main():
    app = TriLingoApp()
    app.run()


if __name__ == "__main__":
    main()

