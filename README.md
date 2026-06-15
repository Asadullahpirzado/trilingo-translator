# 🌐 TriLingo — English · Urdu · Sindhi Translator

A fully **offline**, open-source desktop translation application built in Python.  
Supports bidirectional translation between **English**, **Urdu**, and **Sindhi**  
with a modern GUI, Text-to-Speech, and persistent translation history.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔄 6 Translation Directions | EN↔UR, EN↔SD, UR↔SD |
| 🌍 Offline First | No API key, no internet required |
| 🖥 Modern GUI | Built with Tkinter — cross-platform |
| 🔊 Text-to-Speech | Reads input & output aloud (pyttsx3 / gTTS) |
| 🕵 Auto Language Detection | Unicode-based heuristic detection |
| ⇄ Swap Languages | One click to reverse translation direction |
| 📜 History Panel | SQLite-backed persistent history |
| 📋 Copy to Clipboard | One-click copy of translation |
| 💾 Export History | Save as TXT or CSV |
| 🌙 Dark / Light Theme | Toggle between themes |
| ⌨ Keyboard Shortcuts | Ctrl+Enter = Translate, Ctrl+D = Swap |
| 🔤 Arabic Script Fonts | Proper Urdu/Sindhi Nastaliq rendering |

---

## 📁 Project Structure

```
trilingo/
├── main.py                  # Entry point
├── requirements.txt
├── setup.py
│
├── translator/
│   ├── engine.py            # Core translation logic
│   └── history.py           # SQLite history manager
│
├── tts/
│   └── engine.py            # Text-to-Speech (pyttsx3 + gTTS)
│
├── gui/
│   └── app.py               # Tkinter GUI application
│
├── data/
│   ├── en_ur_dict.py        # English ↔ Urdu dictionary (~300 entries)
│   ├── en_sd_dict.py        # English ↔ Sindhi dictionary (~300 entries)
│   └── ur_sd_dict.py        # Urdu ↔ Sindhi bridge dictionary
│
└── tests/
    └── test_engine.py       # Unit tests
```

---

## 🚀 Quick Start

### 1. Clone / Download

```bash
git clone <your-repo-url>
cd trilingo
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Tkinter** comes pre-installed with Python.  
> On Linux, install it with: `sudo apt install python3-tk`

### 3. Run

```bash
python main.py
```

---

## ⌨ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl + Enter` | Translate |
| `Ctrl + D` | Swap languages |
| `Ctrl + S` | Speak output |
| `Ctrl + L` | Clear all |

---

## 🔊 TTS Setup

TriLingo tries TTS backends in this order:

1. **pyttsx3** — Fully offline. Best for English.
2. **gTTS** — Google TTS (requires internet). Better for Urdu/Sindhi.
3. **espeak** — System fallback on Linux.

Install all for best results:
```bash
pip install pyttsx3 gTTS pygame
```

---

## 🧪 Running Tests

```bash
# With pytest
pip install pytest
pytest tests/ -v

# Without pytest
python tests/test_engine.py
```

---

## 🗂 Translation Quality

The translator uses a **multi-pass dictionary engine**:

1. Full phrase exact match
2. Greedy phrase-first chunking (up to 6-word phrases)
3. Word-by-word token translation
4. English as pivot language for Urdu↔Sindhi (if no direct match)

Each dictionary contains **~300 words and phrases** covering:
- Greetings & common phrases
- Family & people
- Numbers, colors, days, months
- Places, food, nature
- Common verbs and adjectives

---
