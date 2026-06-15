"""
TriLingo GUI Application
=========================
Modern Tkinter-based desktop translator.
Features:
  - English ↔ Urdu ↔ Sindhi (all 6 directions)
  - Auto language detection
  - Swap languages button
  - Text-to-Speech (input and output)
  - Translation history panel with SQLite persistence
  - Copy to clipboard
  - Export history (TXT / CSV)
  - Clear fields
  - Dark / Light theme toggle
  - Keyboard shortcut: Ctrl+Enter to translate
  - Proper Arabic/Urdu/Sindhi RTL font rendering
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime

# Make sure project root is on path (Windows & Linux safe)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from translator.engine  import translate, detect_language, ENGLISH, URDU, SINDHI, LANGUAGE_NAMES
from translator.history import HistoryManager
from tts.engine         import TTSEngine


# ---------------------------------------------------------------------------
# Theme definitions
# ---------------------------------------------------------------------------
THEMES = {
    "dark": {
        "bg":           "#1a1a2e",
        "panel_bg":     "#16213e",
        "input_bg":     "#0f3460",
        "output_bg":    "#0a2540",
        "text_fg":      "#e0e0e0",
        "accent":       "#e94560",
        "accent2":      "#533483",
        "btn_bg":       "#e94560",
        "btn_fg":       "#ffffff",
        "btn_hover":    "#c73652",
        "swap_bg":      "#533483",
        "border":       "#2a2a4a",
        "history_bg":   "#16213e",
        "history_sel":  "#e94560",
        "status_bg":    "#0f3460",
        "label_fg":     "#a0a0c0",
        "title_fg":     "#e94560",
    },
    "light": {
        "bg":           "#f5f7fa",
        "panel_bg":     "#ffffff",
        "input_bg":     "#ffffff",
        "output_bg":    "#f0f4ff",
        "text_fg":      "#1a1a2e",
        "accent":       "#e94560",
        "accent2":      "#533483",
        "btn_bg":       "#e94560",
        "btn_fg":       "#ffffff",
        "btn_hover":    "#c73652",
        "swap_bg":      "#533483",
        "border":       "#d0d5e8",
        "history_bg":   "#f5f7fa",
        "history_sel":  "#e94560",
        "status_bg":    "#e8eaf6",
        "label_fg":     "#555577",
        "title_fg":     "#e94560",
    },
}

LANG_OPTIONS = [
    ("English",  ENGLISH),
    ("Urdu",     URDU),
    ("Sindhi",   SINDHI),
]

# Arabic-script fonts that render well on common OS setups
ARABIC_FONTS = [
    "Noto Nastaliq Urdu",
    "Jameel Noori Nastaleeq",
    "Noto Naskh Arabic",
    "Arabic Typesetting",
    "Segoe UI",   # Windows fallback
    "Arial",      # generic fallback
]

LATIN_FONT = ("Segoe UI", 11) if sys.platform == "win32" else ("Helvetica", 11)


class TriLingoApp:
    """Main application class."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TriLingo — English | Urdu | Sindhi Translator")
        self.root.geometry("1100x720")
        self.root.minsize(800, 600)

        self.theme_name = tk.StringVar(value="dark")
        self.theme      = THEMES["dark"]

        self.from_lang  = tk.StringVar(value=ENGLISH)
        self.to_lang    = tk.StringVar(value=URDU)
        self.auto_detect = tk.BooleanVar(value=False)
        self.tts_busy   = False

        self.history_mgr = HistoryManager()
        self.tts_engine  = TTSEngine()

        self._build_ui()
        self._apply_theme()
        self._bind_shortcuts()
        self._refresh_history()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # -----------------------------------------------------------------------
    # UI Construction
    # -----------------------------------------------------------------------

    def _build_ui(self):
        t = self.theme

        # ── Title bar row ──────────────────────────────────────────────────
        self.title_frame = tk.Frame(self.root, height=52)
        self.title_frame.pack(fill=tk.X, side=tk.TOP)

        self.lbl_logo = tk.Label(
            self.title_frame,
            text="🌐  TriLingo",
            font=("Georgia", 18, "bold"),
            pady=10, padx=18,
        )
        self.lbl_logo.pack(side=tk.LEFT)

        self.lbl_subtitle = tk.Label(
            self.title_frame,
            text="English · Urdu · Sindhi  —  Offline Translator",
            font=("Helvetica", 10),
            pady=10,
        )
        self.lbl_subtitle.pack(side=tk.LEFT, padx=6)

        # Theme toggle button (top-right)
        self.btn_theme = tk.Button(
            self.title_frame,
            text="☀ Light Mode",
            font=("Helvetica", 9),
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            command=self._toggle_theme,
        )
        self.btn_theme.pack(side=tk.RIGHT, padx=12, pady=10)

        # ── Main paned area (translator | history) ────────────────────────
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=6)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Left: translator panel
        self.left_panel = tk.Frame(self.paned)
        self.paned.add(self.left_panel, minsize=580, stretch="always")

        # Right: history panel
        self.right_panel = tk.Frame(self.paned, width=300)
        self.paned.add(self.right_panel, minsize=240, stretch="never")

        self._build_translator_panel()
        self._build_history_panel()

        # ── Status bar ─────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready  •  Ctrl+Enter to translate")
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            anchor=tk.W,
            padx=12,
            pady=4,
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _build_translator_panel(self):
        """Left panel: language selectors, text areas, buttons."""
        p = self.left_panel

        # ── Language selector row ──────────────────────────────────────────
        lang_row = tk.Frame(p)
        lang_row.pack(fill=tk.X, padx=14, pady=(12, 4))

        # FROM
        tk.Label(lang_row, text="FROM", font=("Helvetica", 8, "bold")).pack(side=tk.LEFT)
        self.combo_from = ttk.Combobox(
            lang_row,
            textvariable=self.from_lang,
            values=[name for name, _ in LANG_OPTIONS],
            state="readonly",
            width=12,
            font=("Helvetica", 11),
        )
        # Map display name ↔ code
        self._lang_name_to_code = {name: code for name, code in LANG_OPTIONS}
        self._lang_code_to_name = {code: name for name, code in LANG_OPTIONS}
        self.combo_from.set(self._lang_code_to_name[ENGLISH])
        self.combo_from.pack(side=tk.LEFT, padx=(6, 4))
        self.combo_from.bind("<<ComboboxSelected>>", self._on_lang_change)

        # Auto-detect checkbox
        self.chk_auto = tk.Checkbutton(
            lang_row,
            text="Auto-detect",
            variable=self.auto_detect,
            font=("Helvetica", 9),
            command=self._on_auto_detect_toggle,
        )
        self.chk_auto.pack(side=tk.LEFT, padx=8)

        # SWAP button
        self.btn_swap = tk.Button(
            lang_row,
            text="⇄ Swap",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._swap_languages,
        )
        self.btn_swap.pack(side=tk.LEFT, padx=8)

        # TO
        tk.Label(lang_row, text="TO", font=("Helvetica", 8, "bold")).pack(side=tk.LEFT, padx=(8, 0))
        self.combo_to = ttk.Combobox(
            lang_row,
            textvariable=self.to_lang,
            values=[name for name, _ in LANG_OPTIONS],
            state="readonly",
            width=12,
            font=("Helvetica", 11),
        )
        self.combo_to.set(self._lang_code_to_name[URDU])
        self.combo_to.pack(side=tk.LEFT, padx=(6, 0))
        self.combo_to.bind("<<ComboboxSelected>>", self._on_lang_change)

        # ── Input area ─────────────────────────────────────────────────────
        in_frame = tk.Frame(p, bd=1, relief=tk.SOLID)
        in_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(6, 0))

        in_header = tk.Frame(in_frame)
        in_header.pack(fill=tk.X, padx=6, pady=(4, 0))
        self.lbl_input_lang = tk.Label(
            in_header, text="English", font=("Helvetica", 9, "bold")
        )
        self.lbl_input_lang.pack(side=tk.LEFT)

        # TTS button for input
        self.btn_tts_input = tk.Button(
            in_header,
            text="🔊",
            font=("Helvetica", 11),
            relief=tk.FLAT,
            cursor="hand2",
            padx=4,
            command=self._speak_input,
        )
        self.btn_tts_input.pack(side=tk.RIGHT)

        # Clear input button
        tk.Button(
            in_header,
            text="✕ Clear",
            font=("Helvetica", 8),
            relief=tk.FLAT,
            cursor="hand2",
            padx=4,
            command=self._clear_input,
        ).pack(side=tk.RIGHT, padx=4)

        self.txt_input = tk.Text(
            in_frame,
            height=7,
            wrap=tk.WORD,
            font=("Helvetica", 12),
            bd=0,
            padx=10,
            pady=8,
            undo=True,
        )
        self.txt_input.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 6))

        in_scroll = tk.Scrollbar(in_frame, command=self.txt_input.yview)
        self.txt_input.config(yscrollcommand=in_scroll.set)

        # Char counter
        self.lbl_char_count = tk.Label(in_frame, text="0 chars", font=("Helvetica", 8))
        self.lbl_char_count.pack(side=tk.RIGHT, padx=8, pady=(0, 4))
        self.txt_input.bind("<KeyRelease>", self._on_input_key)

        # ── Action buttons row ─────────────────────────────────────────────
        btn_row = tk.Frame(p)
        btn_row.pack(fill=tk.X, padx=14, pady=6)

        self.btn_translate = tk.Button(
            btn_row,
            text="⚡  Translate",
            font=("Helvetica", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=7,
            command=self._do_translate,
        )
        self.btn_translate.pack(side=tk.LEFT)

        tk.Label(btn_row, text="  Ctrl+Enter", font=("Helvetica", 8)).pack(side=tk.LEFT)

        self.btn_clear_all = tk.Button(
            btn_row,
            text="🗑 Clear All",
            font=("Helvetica", 10),
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=7,
            command=self._clear_all,
        )
        self.btn_clear_all.pack(side=tk.LEFT, padx=10)

        # ── Output area ────────────────────────────────────────────────────
        out_frame = tk.Frame(p, bd=1, relief=tk.SOLID)
        out_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        out_header = tk.Frame(out_frame)
        out_header.pack(fill=tk.X, padx=6, pady=(4, 0))
        self.lbl_output_lang = tk.Label(
            out_header, text="Urdu", font=("Helvetica", 9, "bold")
        )
        self.lbl_output_lang.pack(side=tk.LEFT)

        # TTS button for output
        self.btn_tts_output = tk.Button(
            out_header,
            text="🔊",
            font=("Helvetica", 11),
            relief=tk.FLAT,
            cursor="hand2",
            padx=4,
            command=self._speak_output,
        )
        self.btn_tts_output.pack(side=tk.RIGHT)

        # Copy button
        self.btn_copy = tk.Button(
            out_header,
            text="📋 Copy",
            font=("Helvetica", 8),
            relief=tk.FLAT,
            cursor="hand2",
            padx=4,
            command=self._copy_output,
        )
        self.btn_copy.pack(side=tk.RIGHT, padx=4)

        # Arabic script text needs special font and RTL
        self.txt_output = tk.Text(
            out_frame,
            height=7,
            wrap=tk.WORD,
            font=("Helvetica", 13),
            bd=0,
            padx=10,
            pady=8,
            state=tk.DISABLED,
        )
        self.txt_output.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 6))

        out_scroll = tk.Scrollbar(out_frame, command=self.txt_output.yview)
        self.txt_output.config(yscrollcommand=out_scroll.set)

    def _build_history_panel(self):
        """Right panel: translation history."""
        p = self.right_panel

        # Header
        hist_header = tk.Frame(p)
        hist_header.pack(fill=tk.X, padx=8, pady=(12, 4))

        tk.Label(
            hist_header, text="📜 History",
            font=("Helvetica", 11, "bold"),
        ).pack(side=tk.LEFT)

        tk.Label(
            hist_header,
            text=f"({self.history_mgr.count()} entries)",
            font=("Helvetica", 8),
        ).pack(side=tk.LEFT, padx=4)

        # Export / Clear buttons
        btn_sub = tk.Frame(p)
        btn_sub.pack(fill=tk.X, padx=8, pady=(0, 4))

        tk.Button(
            btn_sub, text="Export TXT",
            font=("Helvetica", 8),
            relief=tk.FLAT,
            cursor="hand2",
            padx=6, pady=2,
            command=lambda: self._export_history("txt"),
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_sub, text="Export CSV",
            font=("Helvetica", 8),
            relief=tk.FLAT,
            cursor="hand2",
            padx=6, pady=2,
            command=lambda: self._export_history("csv"),
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            btn_sub, text="🗑 Clear",
            font=("Helvetica", 8),
            relief=tk.FLAT,
            cursor="hand2",
            padx=6, pady=2,
            command=self._clear_history,
        ).pack(side=tk.RIGHT)

        # Listbox + scrollbar
        list_frame = tk.Frame(p)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        scroll_y = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.history_list = tk.Listbox(
            list_frame,
            font=("Helvetica", 9),
            selectmode=tk.SINGLE,
            yscrollcommand=scroll_y.set,
            activestyle="dotbox",
            bd=0,
            highlightthickness=0,
        )
        scroll_y.config(command=self.history_list.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_list.pack(fill=tk.BOTH, expand=True)

        self.history_list.bind("<<ListboxSelect>>", self._on_history_select)
        self.history_list.bind("<Double-Button-1>", self._on_history_double_click)

        # Detail area
        tk.Label(p, text="Selected Entry:", font=("Helvetica", 8)).pack(
            anchor=tk.W, padx=8, pady=(8, 0)
        )
        self.txt_hist_detail = tk.Text(
            p,
            height=6,
            font=("Helvetica", 9),
            wrap=tk.WORD,
            bd=1,
            relief=tk.SOLID,
            padx=6,
            pady=4,
            state=tk.DISABLED,
        )
        self.txt_hist_detail.pack(fill=tk.X, padx=8, pady=(2, 6))

        tk.Button(
            p, text="↩ Restore to Translator",
            font=("Helvetica", 9),
            relief=tk.FLAT,
            cursor="hand2",
            padx=8, pady=4,
            command=self._restore_from_history,
        ).pack(pady=(0, 8))

        # Store history records for reference
        self._history_records = []

    # -----------------------------------------------------------------------
    # Theme
    # -----------------------------------------------------------------------

    def _apply_theme(self):
        t = self.theme
        r = self.root

        r.configure(bg=t["bg"])
        self.title_frame.configure(bg=t["panel_bg"])
        self.lbl_logo.configure(bg=t["panel_bg"], fg=t["title_fg"])
        self.lbl_subtitle.configure(bg=t["panel_bg"], fg=t["label_fg"])
        self.btn_theme.configure(
            bg=t["accent2"], fg=t["btn_fg"],
            activebackground=t["btn_hover"],
            activeforeground=t["btn_fg"],
        )

        self.left_panel.configure(bg=t["bg"])
        self.right_panel.configure(bg=t["panel_bg"])
        self.paned.configure(bg=t["border"])

        # Language row widgets
        for w in self.left_panel.winfo_children():
            self._style_frame_recursive(w, t)

        # Input text area
        self.txt_input.configure(
            bg=t["input_bg"], fg=t["text_fg"],
            insertbackground=t["accent"],
            selectbackground=t["accent"],
        )
        # Output text area
        self.txt_output.configure(
            bg=t["output_bg"], fg=t["text_fg"],
        )

        # Translate button
        self.btn_translate.configure(
            bg=t["btn_bg"], fg=t["btn_fg"],
            activebackground=t["btn_hover"],
        )
        # Swap button
        self.btn_swap.configure(
            bg=t["swap_bg"], fg=t["btn_fg"],
            activebackground=t["accent2"],
        )

        # History panel
        for w in self.right_panel.winfo_children():
            self._style_frame_recursive(w, t)

        self.history_list.configure(
            bg=t["history_bg"],
            fg=t["text_fg"],
            selectbackground=t["history_sel"],
            selectforeground="#ffffff",
        )
        self.txt_hist_detail.configure(
            bg=t["panel_bg"], fg=t["text_fg"],
        )

        # Status bar
        self.status_bar.configure(bg=t["status_bg"], fg=t["label_fg"])

        # Combobox style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
            fieldbackground=t["input_bg"],
            background=t["input_bg"],
            foreground=t["text_fg"],
            selectbackground=t["accent"],
            selectforeground="#ffffff",
        )

    def _style_frame_recursive(self, widget, t):
        """Recursively style frames and labels."""
        cls = widget.__class__.__name__
        try:
            if cls == "Frame":
                widget.configure(bg=t["bg"] if widget.master == self.left_panel else t["panel_bg"])
            elif cls == "Label":
                parent_bg = t["panel_bg"] if widget.master.master == self.right_panel else t["bg"]
                widget.configure(bg=t["bg"], fg=t["label_fg"])
            elif cls == "Checkbutton":
                widget.configure(bg=t["bg"], fg=t["text_fg"],
                                 selectcolor=t["input_bg"],
                                 activebackground=t["bg"],
                                 activeforeground=t["text_fg"])
            elif cls == "Button":
                if widget not in (self.btn_translate, self.btn_swap, self.btn_theme):
                    widget.configure(
                        bg=t["panel_bg"], fg=t["text_fg"],
                        activebackground=t["accent"],
                        activeforeground="#fff",
                    )
        except tk.TclError:
            pass

        for child in widget.winfo_children():
            self._style_frame_recursive(child, t)

    def _toggle_theme(self):
        if self.theme_name.get() == "dark":
            self.theme_name.set("light")
            self.theme = THEMES["light"]
            self.btn_theme.configure(text="🌙 Dark Mode")
        else:
            self.theme_name.set("dark")
            self.theme = THEMES["dark"]
            self.btn_theme.configure(text="☀ Light Mode")
        self._apply_theme()

    # -----------------------------------------------------------------------
    # Language helpers
    # -----------------------------------------------------------------------

    def _get_from_code(self) -> str:
        name = self.combo_from.get()
        return self._lang_name_to_code.get(name, ENGLISH)

    def _get_to_code(self) -> str:
        name = self.combo_to.get()
        return self._lang_name_to_code.get(name, URDU)

    def _on_lang_change(self, event=None):
        from_code = self._get_from_code()
        to_code   = self._get_to_code()
        self.lbl_input_lang.configure(text=LANGUAGE_NAMES[from_code])
        self.lbl_output_lang.configure(text=LANGUAGE_NAMES[to_code])
        self._update_text_fonts(from_code, to_code)

    def _update_text_fonts(self, from_code: str, to_code: str):
        """Switch fonts to Arabic-script when language requires it."""
        arabic_langs = {URDU, SINDHI}

        if from_code in arabic_langs:
            self.txt_input.configure(font=(ARABIC_FONTS[0], 14))
        else:
            self.txt_input.configure(font=("Helvetica", 12))

        if to_code in arabic_langs:
            self.txt_output.configure(font=(ARABIC_FONTS[0], 14))
        else:
            self.txt_output.configure(font=("Helvetica", 13))

    def _swap_languages(self):
        from_name = self.combo_from.get()
        to_name   = self.combo_to.get()

        # Swap combos
        self.combo_from.set(to_name)
        self.combo_to.set(from_name)

        # Swap text content
        input_text  = self.txt_input.get("1.0", tk.END).strip()
        output_text = self._get_output_text()

        self._set_input(output_text)
        self._set_output(input_text)

        self._on_lang_change()
        self._set_status("Languages swapped.")

    def _on_auto_detect_toggle(self):
        if self.auto_detect.get():
            self.combo_from.configure(state="disabled")
            self._set_status("Auto-detect ON — language will be detected on translate.")
        else:
            self.combo_from.configure(state="readonly")
            self._set_status("Auto-detect OFF.")

    # -----------------------------------------------------------------------
    # Translation
    # -----------------------------------------------------------------------

    def _do_translate(self, event=None):
        text = self.txt_input.get("1.0", tk.END).strip()
        if not text:
            self._set_status("⚠  Please enter text to translate.")
            return

        from_code = self._get_from_code()
        to_code   = self._get_to_code()

        # Auto-detect
        if self.auto_detect.get():
            from_code = detect_language(text)
            detected_name = LANGUAGE_NAMES[from_code]
            self.combo_from.configure(state="normal")
            self.combo_from.set(self._lang_code_to_name[from_code])
            self.combo_from.configure(state="disabled")
            self._set_status(f"Detected: {detected_name}")

        if from_code == to_code:
            self._set_output(text)
            self._set_status("Source and target languages are the same.")
            return

        self._set_status("Translating…")
        self.btn_translate.configure(state=tk.DISABLED)

        def _run():
            try:
                result = translate(text, from_code, to_code)
                self.root.after(0, lambda: self._show_result(
                    result, text, from_code, to_code
                ))
            except Exception as exc:
                self.root.after(0, lambda: self._set_status(f"Error: {exc}"))
                self.root.after(0, lambda: self.btn_translate.configure(state=tk.NORMAL))

        threading.Thread(target=_run, daemon=True).start()

    def _show_result(self, result: str, source: str, from_code: str, to_code: str):
        self._set_output(result)
        self.btn_translate.configure(state=tk.NORMAL)

        fr_name = LANGUAGE_NAMES[from_code]
        to_name = LANGUAGE_NAMES[to_code]
        self._set_status(f"✓  Translated  {fr_name} → {to_name}")

        # Save to history
        self.history_mgr.add(from_code, to_code, source, result)
        self._refresh_history()
        self._update_text_fonts(from_code, to_code)

    # -----------------------------------------------------------------------
    # Text area helpers
    # -----------------------------------------------------------------------

    def _set_input(self, text: str):
        self.txt_input.delete("1.0", tk.END)
        self.txt_input.insert("1.0", text)

    def _set_output(self, text: str):
        self.txt_output.configure(state=tk.NORMAL)
        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert("1.0", text)
        self.txt_output.configure(state=tk.DISABLED)

    def _get_output_text(self) -> str:
        self.txt_output.configure(state=tk.NORMAL)
        text = self.txt_output.get("1.0", tk.END).strip()
        self.txt_output.configure(state=tk.DISABLED)
        return text

    def _clear_input(self):
        self.txt_input.delete("1.0", tk.END)
        self._set_status("Input cleared.")

    def _clear_all(self):
        self._set_input("")
        self._set_output("")
        self._set_status("Cleared.")

    def _copy_output(self):
        text = self._get_output_text()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self._set_status("✓  Translation copied to clipboard.")
        else:
            self._set_status("Nothing to copy yet.")

    def _on_input_key(self, event=None):
        n = len(self.txt_input.get("1.0", tk.END).strip())
        self.lbl_char_count.configure(text=f"{n} chars")

    # -----------------------------------------------------------------------
    # TTS
    # -----------------------------------------------------------------------

    def _speak_input(self):
        text = self.txt_input.get("1.0", tk.END).strip()
        lang = self._get_from_code()
        self._speak(text, lang)

    def _speak_output(self):
        text = self._get_output_text()
        lang = self._get_to_code()
        self._speak(text, lang)

    def _speak(self, text: str, lang: str):
        if not text:
            self._set_status("⚠  No text to speak.")
            return
        if self.tts_busy:
            self._set_status("⚠  Already speaking…")
            return
        self.tts_busy = True
        self._set_status(f"🔊  Speaking ({LANGUAGE_NAMES[lang]})…")

        def _done():
            self.tts_busy = False
            self.root.after(0, lambda: self._set_status("Ready"))

        self.tts_engine.speak(text, lang, callback=_done)

    # -----------------------------------------------------------------------
    # History
    # -----------------------------------------------------------------------

    def _refresh_history(self):
        self.history_list.delete(0, tk.END)
        records = self.history_mgr.fetch_all(limit=150)
        self._history_records = records
        for row in records:
            rid, created, fr, to, src, res = row
            display = f"[{fr}→{to}]  {src[:30]}{'…' if len(src)>30 else ''}"
            self.history_list.insert(tk.END, display)

        # Update header count
        for w in self.right_panel.winfo_children():
            if isinstance(w, tk.Frame):
                for child in w.winfo_children():
                    if isinstance(child, tk.Label) and "entries" in (child.cget("text") or ""):
                        child.configure(text=f"({self.history_mgr.count()} entries)")

    def _on_history_select(self, event=None):
        sel = self.history_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._history_records):
            return
        rid, created, fr, to, src, res = self._history_records[idx]
        detail = (
            f"Date:   {created}\n"
            f"From:   {LANGUAGE_NAMES.get(fr, fr)}\n"
            f"To:     {LANGUAGE_NAMES.get(to, to)}\n\n"
            f"Source:\n{src}\n\n"
            f"Result:\n{res}"
        )
        self.txt_hist_detail.configure(state=tk.NORMAL)
        self.txt_hist_detail.delete("1.0", tk.END)
        self.txt_hist_detail.insert("1.0", detail)
        self.txt_hist_detail.configure(state=tk.DISABLED)

    def _on_history_double_click(self, event=None):
        self._restore_from_history()

    def _restore_from_history(self):
        sel = self.history_list.curselection()
        if not sel:
            self._set_status("Select a history entry first.")
            return
        idx = sel[0]
        if idx >= len(self._history_records):
            return
        rid, created, fr, to, src, res = self._history_records[idx]

        self._set_input(src)
        self._set_output(res)
        self.combo_from.set(self._lang_code_to_name.get(fr, fr))
        self.combo_to.set(self._lang_code_to_name.get(to, to))
        self._on_lang_change()
        self._set_status(f"Restored from history  [{LANGUAGE_NAMES.get(fr)}→{LANGUAGE_NAMES.get(to)}]")

    def _clear_history(self):
        if messagebox.askyesno("Clear History", "Delete all translation history?"):
            self.history_mgr.clear_all()
            self._refresh_history()
            self.txt_hist_detail.configure(state=tk.NORMAL)
            self.txt_hist_detail.delete("1.0", tk.END)
            self.txt_hist_detail.configure(state=tk.DISABLED)
            self._set_status("History cleared.")

    def _export_history(self, fmt: str):
        ext = ".txt" if fmt == "txt" else ".csv"
        fp = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[("Text file", "*.txt"), ("CSV file", "*.csv"), ("All files", "*.*")],
            title="Export Translation History",
            initialfile=f"trilingo_history_{datetime.date.today()}{ext}",
        )
        if fp:
            self.history_mgr.export_to_file(fp, fmt)
            self._set_status(f"✓  History exported to {os.path.basename(fp)}")

    # -----------------------------------------------------------------------
    # Keyboard shortcuts
    # -----------------------------------------------------------------------

    def _bind_shortcuts(self):
        self.root.bind("<Control-Return>", self._do_translate)
        self.root.bind("<Control-s>", lambda e: self._speak_output())
        self.root.bind("<Control-d>", lambda e: self._swap_languages())
        self.root.bind("<Control-l>", lambda e: self._clear_all())

    # -----------------------------------------------------------------------
    # Utilities
    # -----------------------------------------------------------------------

    def _set_status(self, msg: str):
        self.status_var.set(f"  {msg}")

    def _on_close(self):
        self.history_mgr.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
