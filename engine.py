"""
TriLingo Text-to-Speech Engine
================================
Provides offline and online TTS with automatic fallback.

Priority order:
  1. pyttsx3  — fully offline, supports multiple voices
  2. gTTS     — online (Google TTS), better quality for non-Latin scripts
  3. espeak   — system fallback (Linux)
  4. Silent   — graceful no-op if nothing is available
"""

import os
import sys
import threading
import tempfile

# Language code → BCP-47 tag for gTTS / espeak
LANG_TTS_MAP = {
    "en": {"gtts": "en",    "espeak": "en",     "pyttsx3": "english"},
    "ur": {"gtts": "ur",    "espeak": "ur",     "pyttsx3": "urdu"},
    "sd": {"gtts": "sd",    "espeak": "sd",     "pyttsx3": "sindhi"},
}

# Try importing engines once at module level
_PYTTSX3_AVAILABLE = False
_GTTS_AVAILABLE    = False
_PYGAME_AVAILABLE  = False

try:
    import pyttsx3
    _PYTTSX3_AVAILABLE = True
except ImportError:
    pass

try:
    from gtts import gTTS
    _GTTS_AVAILABLE = True
except ImportError:
    pass

try:
    import pygame
    _PYGAME_AVAILABLE = True
except ImportError:
    pass


class TTSEngine:
    """
    Unified TTS interface with automatic backend selection.
    All speak() calls are non-blocking (run in a background thread).
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._pyttsx3_engine = None
        self._init_pyttsx3()

    def _init_pyttsx3(self):
        """Initialise pyttsx3 lazily."""
        if not _PYTTSX3_AVAILABLE:
            return
        try:
            self._pyttsx3_engine = pyttsx3.init()
            self._pyttsx3_engine.setProperty("rate", 150)
            self._pyttsx3_engine.setProperty("volume", 1.0)
        except Exception:
            self._pyttsx3_engine = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(self, text: str, lang_code: str = "en", callback=None):
        """
        Speak `text` in the given language.
        Runs in a background thread so the GUI stays responsive.

        Args:
            text:      Text to read aloud.
            lang_code: Language code ('en', 'ur', 'sd').
            callback:  Optional callable invoked when speech finishes.
        """
        if not text or not text.strip():
            return

        t = threading.Thread(
            target=self._speak_threaded,
            args=(text, lang_code, callback),
            daemon=True,
        )
        t.start()

    def _speak_threaded(self, text: str, lang_code: str, callback):
        """Internal: runs in background thread."""
        with self._lock:
            success = False

            # Try pyttsx3 first (fully offline)
            if self._pyttsx3_engine and lang_code == "en":
                success = self._speak_pyttsx3(text)

            # Fall back to gTTS (online) for Urdu/Sindhi or pyttsx3 failure
            if not success and _GTTS_AVAILABLE:
                success = self._speak_gtts(text, lang_code)

            # Last resort: espeak system call
            if not success:
                self._speak_espeak(text, lang_code)

        if callback:
            try:
                callback()
            except Exception:
                pass

    def _speak_pyttsx3(self, text: str) -> bool:
        """Speak using pyttsx3 (offline, English-focused)."""
        try:
            self._pyttsx3_engine.say(text)
            self._pyttsx3_engine.runAndWait()
            return True
        except Exception:
            return False

    def _speak_gtts(self, text: str, lang_code: str) -> bool:
        """Speak using gTTS → save to temp file → play with pygame or os."""
        try:
            tts_lang = LANG_TTS_MAP.get(lang_code, {}).get("gtts", "en")
            tts = gTTS(text=text, lang=tts_lang, slow=False)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name

            tts.save(tmp_path)

            played = False

            # Try pygame for playback
            if _PYGAME_AVAILABLE:
                try:
                    pygame.mixer.init()
                    pygame.mixer.music.load(tmp_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        import time
                        time.sleep(0.1)
                    pygame.mixer.music.unload()
                    played = True
                except Exception:
                    pass

            # Try system player
            if not played:
                if sys.platform == "win32":
                    os.system(f'start /wait "" "{tmp_path}"')
                elif sys.platform == "darwin":
                    os.system(f'afplay "{tmp_path}"')
                else:
                    os.system(f'mpg123 -q "{tmp_path}" 2>/dev/null || '
                              f'ffplay -nodisp -autoexit "{tmp_path}" 2>/dev/null || '
                              f'aplay "{tmp_path}" 2>/dev/null')

            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            return True

        except Exception:
            return False

    def _speak_espeak(self, text: str, lang_code: str):
        """Last-resort: use system espeak."""
        try:
            esp_lang = LANG_TTS_MAP.get(lang_code, {}).get("espeak", "en")
            # espeak handles Latin scripts well; for Arabic-script use -v en as fallback
            os.system(f'espeak -v {esp_lang} "{text}" 2>/dev/null || '
                      f'espeak -v en "{text}" 2>/dev/null')
        except Exception:
            pass

    @staticmethod
    def is_available() -> dict:
        """Return dict of available TTS backends."""
        return {
            "pyttsx3": _PYTTSX3_AVAILABLE,
            "gtts":    _GTTS_AVAILABLE,
            "pygame":  _PYGAME_AVAILABLE,
        }
