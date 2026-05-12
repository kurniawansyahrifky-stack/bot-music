# anony/plugins/antibc_extra.py

import re
import time

# ================= STORAGE =================
user_last_msg = {}
user_last_text = {}

# ================= NORMALIZE =================
def normalize(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    replace_map = {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a"
    }

    for k, v in replace_map.items():
        text = text.replace(k, v)

    text = re.sub(r"(.)\1{2,}", r"\1", text)

    slang_map = {
        "crt": "chat",
        "y": "yuk",
        "yu": "yuk",
        "yug": "yuk",
        "dm": "chat",
        "pm": "chat",
        "vcc": "vc",
        "vcg": "vc",
        "byo": "byoh",
        "biyouh": "byoh",
        "biyoh": "byoh",
        "tmoh": "temo",
        "fwbh": "fwb",
    }

    for k, v in slang_map.items():
        text = text.replace(k, v)

    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ================= WORD MATCH =================
def has_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


# ================= BYOH SUPER =================
def detect_byoh_super(text: str) -> bool:
    patterns = [
        r"b\W*i?\W*y?\W*o+\W*h+",
        r"b\W*i?\W*y?\W*o+\W*u+\W*h+",
        r"b\W*i?\W*y?\W*o+\W*c\W*h+",
        r"b[\W_]*i?[\W_]*y?[\W_]*o+[\W_]*h+",
    ]
    return any(re.search(p, text) for p in patterns)


# ================= KEYWORDS =================
SEX_WORDS = [
    "sex", "seks", "ngentot", "ngewe", "coli", "colmek",
    "sange", "horny", "birahi", "ml", "ewe", "entot"
]

VCS_WORDS = [
    "vcs", "vc", "call", "video", "vidcall"
]

SERVICE_WORDS = [
    "open", "order", "booking", "ready",
    "available", "gas", "chat"
]

PROMO_WORDS = [
    "murah", "murmer", "promo", "diskon",
    "harga", "langsung", "cepet"
]

RELATION_WORDS = [
    "temenin", "cari", "butuh", "mau",
    "need", "partner", "fwb"
]

EXTRA_WORDS = [
    "byoh", "bo", "openbo", "pap", "rate",
    "bugil", "telanjang", "send", "ss",
    "tmoh", "fwb", "bonus", "gede"
]

KEYWORDS = list(set(
    SEX_WORDS +
    VCS_WORDS +
    SERVICE_WORDS +
    PROMO_WORDS +
    RELATION_WORDS +
    EXTRA_WORDS
))


# ================= PATTERNS =================
PATTERNS = [
    r"s[\s\W_]*e[\s\W_]*x",
    r"n[\s\W_]*g[\s\W_]*e[\s\W_]*w[\s\W_]*e",
    r"c[\s\W_]*o[\s\W_]*l[\s\W_]*i",
    r"v[\s\W_]*c[\s\W_]*s",
    r"o[\s\W_]*p[\s\W_]*e[\s\W_]*n[\s\W_]*b[\s\W_]*o",
    r"t[\s\W_]*e[\s\W_]*m[\s\W_]*e[\s\W_]*n[\s\W_]*i[\s\W_]*n",
]


# ================= DETECTORS =================
def promo_detector(text: str) -> bool:
    return (
        any(has_word(text, p) for p in PROMO_WORDS)
        and any(has_word(text, a) for a in ["chat", "gas", "langsung"])
    )


def suspicious_sentence(text: str) -> bool:
    return (
        any(has_word(text, t) for t in RELATION_WORDS)
        and any(has_word(text, a) for a in ["chat", "vc", "malam", "call"])
    )


def spam_format(text: str) -> bool:
    return bool(re.search(r"[a-z]*\d+[a-z]*\d+[a-z]*", text))


def is_gibberish(text: str) -> bool:
    words = text.split()
    if len(words) >= 5:
        long_words = [w for w in words if len(w) > 7]
        if len(long_words) >= 2:
            return True
    return False


# ================= FLOOD DETECTOR =================
def is_flood(user_id: int) -> bool:
    now = time.time()

    if user_id in user_last_msg:
        if now - user_last_msg[user_id] < 3:
            user_last_msg[user_id] = now
            return True

    user_last_msg[user_id] = now
    return False


# ================= DUPLICATE DETECTOR =================
def is_duplicate(user_id: int, text: str) -> bool:
    if user_id in user_last_text:
        if text == user_last_text[user_id]:
            return True

    user_last_text[user_id] = text
    return False


# ================= MAIN DETECTOR =================
def extra_detect(text: str, user_id: int = 0):
    if not text:
        return None

    raw = normalize(text)
    score = 0

    # BYOH
    if detect_byoh_super(raw):
        score += 3

    # regex patterns
    for p in PATTERNS:
        if re.search(p, raw):
            score += 3

    # keywords
    for k in KEYWORDS:
        if has_word(raw, k):
            score += 1

    # kombinasi mesum + service
    if (
        any(has_word(raw, k) for k in SEX_WORDS + VCS_WORDS)
        and any(has_word(raw, s) for s in SERVICE_WORDS)
    ):
        score += 4

    # promo
    if promo_detector(raw):
        score += 3

    # suspicious sentence
    if suspicious_sentence(raw):
        score += 2

    # hard combos
    if has_word(raw, "temenin") and has_word(raw, "chat"):
        score += 2

    if has_word(raw, "openbo"):
        score += 0

    if has_word(raw, "fwb"):
        score += 4

    if spam_format(raw):
        score += 2

    if is_gibberish(raw):
        score += 1

    # behavior
    if user_id:
        if is_flood(user_id):
            score += 1

        if is_duplicate(user_id, raw):
            score += 2

    # threshold
    if score >= 3:
        return f"Extra Score {score}"

    return None
