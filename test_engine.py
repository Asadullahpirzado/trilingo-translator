"""
TriLingo — Unit Tests
Run with: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from translator.engine import (
    translate, detect_language,
    ENGLISH, URDU, SINDHI
)


class TestEnglishToUrdu:
    def test_single_word(self):
        assert translate("hello", ENGLISH, URDU) == "ہیلو"

    def test_phrase(self):
        result = translate("good morning", ENGLISH, URDU)
        assert result == "صبح بخیر"

    def test_multiword_sentence(self):
        result = translate("how are you", ENGLISH, URDU)
        assert result == "آپ کیسے ہیں"

    def test_number(self):
        assert translate("one", ENGLISH, URDU) == "ایک"

    def test_color(self):
        assert translate("red", ENGLISH, URDU) == "سرخ"


class TestUrduToEnglish:
    def test_single_word(self):
        assert translate("ہیلو", URDU, ENGLISH) == "hello"

    def test_number_reverse(self):
        assert translate("ایک", URDU, ENGLISH) == "one"


class TestEnglishToSindhi:
    def test_single_word(self):
        assert translate("hello", ENGLISH, SINDHI) == "هيلو"

    def test_greeting(self):
        result = translate("good morning", ENGLISH, SINDHI)
        assert result == "سٿري صبح"

    def test_number(self):
        assert translate("two", ENGLISH, SINDHI) == "ٻه"


class TestSindhiToEnglish:
    def test_single_word(self):
        result = translate("هيلو", SINDHI, ENGLISH)
        assert result == "hello"


class TestUrduToSindhi:
    def test_greeting(self):
        result = translate("ہیلو", URDU, SINDHI)
        assert result == "هيلو"

    def test_number(self):
        result = translate("ایک", URDU, SINDHI)
        assert result == "هڪ"


class TestSindhiToUrdu:
    def test_greeting(self):
        result = translate("هيلو", SINDHI, URDU)
        assert result == "ہیلو"


class TestSameLanguage:
    def test_en_to_en(self):
        assert translate("hello", ENGLISH, ENGLISH) == "hello"

    def test_ur_to_ur(self):
        assert translate("ہیلو", URDU, URDU) == "ہیلو"


class TestEmptyInput:
    def test_empty_string(self):
        assert translate("", ENGLISH, URDU) == ""

    def test_whitespace(self):
        assert translate("   ", ENGLISH, URDU) == ""


class TestDetectLanguage:
    def test_detect_english(self):
        assert detect_language("hello world") == ENGLISH

    def test_detect_urdu(self):
        assert detect_language("ہیلو") == URDU

    def test_detect_sindhi(self):
        assert detect_language("هيلو") in (URDU, SINDHI)  # close scripts

    def test_detect_empty(self):
        assert detect_language("") == ENGLISH


if __name__ == "__main__":
    # Run basic smoke tests without pytest
    tests_passed = 0
    tests_failed = 0

    checks = [
        (translate("hello",        ENGLISH, URDU),   "ہیلو",       "EN→UR: hello"),
        (translate("good morning", ENGLISH, URDU),   "صبح بخیر",   "EN→UR: good morning"),
        (translate("hello",        ENGLISH, SINDHI), "هيلو",       "EN→SD: hello"),
        (translate("ہیلو",          URDU,    ENGLISH),"hello",      "UR→EN: hello"),
        (translate("ایک",           URDU,    SINDHI), "هڪ",         "UR→SD: one"),
        (translate("",             ENGLISH, URDU),   "",           "Empty string"),
        (translate("hello",        ENGLISH, ENGLISH),"hello",      "Same lang"),
        (detect_language("hello"), ENGLISH,                        "Detect EN"),
        (detect_language("ہیلو"),   URDU,                           "Detect UR"),
    ]

    for result, expected, label in checks:
        if result == expected:
            print(f"  ✓  {label}")
            tests_passed += 1
        else:
            print(f"  ✗  {label}  got={repr(result)}  expected={repr(expected)}")
            tests_failed += 1

    print(f"\n{tests_passed} passed, {tests_failed} failed.")
