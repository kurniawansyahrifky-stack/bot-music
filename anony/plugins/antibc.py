# anony/plugins/antibc.py

import asyncio
import aiohttp
import difflib
import re
import time
import unicodedata

from collections import defaultdict, deque
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message
from anony.plugins.antispam_extra import extra_detect
from anony import app, db, config


# =========================================================
# OPTIONAL MODULES
# =========================================================

try:
    from Levenshtein import distance as levenshtein_distance
except Exception:
    levenshtein_distance = None

try:
    from unidecode import unidecode
except Exception:
    def unidecode(x):
        return x


# =========================================================
# CONFIG
# =========================================================

OWNER_ID = getattr(config, "OWNER_ID", 0)
SUDO_USERS = getattr(config, "SUDO_USERS", []) or []

# Pakai API key dari config.py:
# OPENAI_API_KEY = "sk-xxxx"
OPENAI_API_KEY = getattr(config, "OPENAI_API_KEY", None)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4.1-mini"

# Threshold
REPEAT_LIMIT = 3
REPEAT_WINDOW = 120

SIMILAR_LIMIT = 4
SIMILAR_WINDOW = 180

FORWARD_LIMIT = 3
FORWARD_WINDOW = 60

CROSS_GROUP_LIMIT = 4
CROSS_GROUP_WINDOW = 180

FAST_MESSAGE_LIMIT = 6
FAST_MESSAGE_WINDOW = 10


# =========================================================
# CACHE
# =========================================================

USER_MESSAGE_CACHE = defaultdict(lambda: deque(maxlen=50))
USER_FORWARD_CACHE = defaultdict(lambda: deque(maxlen=30))
USER_CROSS_CACHE = defaultdict(lambda: deque(maxlen=100))
USER_FAST_CACHE = defaultdict(lambda: deque(maxlen=20))
LAST_CHAT_MESSAGE = {}
LOCKS = defaultdict(asyncio.Lock)


# =========================================================
# HARD BLACKLIST 18+ / PROMOSI / ANTIBROADCAST SUPER TAJAM
# =========================================================
HARD_BLACKLIST = [
    # =========================
    # KONTEN DEWASA
    # =========================
    "bokep", "bkp", "ngentot", "entot", "memek", "mmk",
    "kontol", "kntl", "coli", "crot", "sange", "horny",
    "vcs", "vcs yuk", "open vcs", "open bo", "bo",
    "on cam", "oncam", "vidcall sex", "call sex",
    "omek", "ome tv", "ometv", "onlyfans",
    "biyoh", "byoh", "dibiyoh", "dbyoh", "dbyo",
    "ngocok", "emut", "sampe crot", "smean",
    "tidurin dong", "manjain aku", "liat aku",
    "liatin aku", "colmek", "pap tt", "pap vc",

    # =========================
    # PROMOSI / JUALAN
    # =========================
    "vip", "premium", "promo", "murah", "diskon",
    "fresh media", "freshmedia", "full video",
    "full vid", "full no sensor", "koleksi pribadi",
    "cek bio", "klik link", "join grup", "join gc",
    "join channel", "link ada di bio", "open member",
    "open slot", "slot terbatas", "admin fast respon",

    # =========================
    # AJAKAN CHAT / PM
    # =========================
    "dm aku", "dm ya", "pc aku", "pc ya",
    "chat aku", "chat ya", "pm aku",
    "pf aku", "cek pf", "cek profil",
    "chat dong", "chat yuk", "pc yuk",
    "open pc", "oppen pc", "open dm",
    "tmOh", "gasak", "becek", "buka",
    "snge", "Fwbh", "Tmo", "pilih",
    "pingin", "ubot", "tmooo", "callcek",
    "udah gatahan", "bonus", "gede", "smp"
    "sngt", "kuat lama", "anu", "ahat",
    # =========================
    # POLA BROADCAST MENFESS
    # =========================
    "gabut", "gabut nih", "gabut banget",
    "bosen", "bosen nih", "bosen banget",
    "temenin aku", "temenin dong",
    "kiww ganteng", "kiww",
    "call yu", "call yuk",
    "yang lucu", "yang ganteng",
    "need abang", "need cwo", "need cwk",
    "need partner", "need teman",
    "siniii", "sinii", "sinii", "sini buru",
    "langsung sayang", "langsung gas",
    "free", "fr3", "fr33",
    "open", "open nih",
    "ada yang", "mn yg", "mana yang",
    "ayo", "ayoo", "yuk", "yu",
    "siapa mau", "mau ga",
    "kuy", "kuyy",

    # =========================
    # BAIT UMUM
    # =========================
    "lagi sendiri", "sendirian nih",
    "lagi kesepian", "kesepian",
    "lagi dingin", "dingin banget",
    "baru putus", "butuh perhatian",
    "ga bisa tidur", "insomnia",
    "cari teman", "cari cwo", "cari cwk",
    "cari yang serius",
    "jkt ada?", "yang di jkt",
    "yang domisili", "dom mana",
    "yang tinggi", "yang kurus",
    "yang bucin", "yang setia",
    "yang ga ghosting",
]

REGEX_PATTERNS = [
    # =========================
    # DEWASA
    # =========================
    r"b[o0]k[e3]p",
    r"v[c(]s",
    r"open\s*vcs",
    r"open\s*bo",
    r"onlyf[a4]ns?",
    r"on\s*cam",
    r"biy[o0]h",
    r"by[o0]h",
    r"dby[o0]h?",
    r"need\s*abang",
    r"need\s*cwo",
    r"need\s*cwk",
    r"sampe\s*crot",
    r"liat(in)?\s*aku",
    r"tidurin\s*dong",

    # =========================
    # PROMOSI
    # =========================
    r"cek\s*bio",
    r"cek\s*pf",
    r"pf\s*aku",
    r"klik\s*link",
    r"join\s*(grup|group|gc|channel)",
    r"full\s*(video|vid)",
    r"fresh\s*media",

    # =========================
    # AJAKAN CHAT
    # =========================
    r"dm\s*a[kq]u",
    r"pc\s*a[kq]u",
    r"chat\s*a[kq]u",
    r"pm\s*a[kq]u",
    r"chat\s*dong",
    r"chat\s*yuk",
    r"open\s*pc",
    r"oppen\s*pc",

    # =========================
    # BROADCAST MENFESS
    # =========================
    r"gabut+",
    r"bosen+",
    r"temenin\s*a[kq]u",
    r"call\s*y[uqk]",
    r"yang\s*lucu",
    r"yang\s*ganteng",
    r"fr[3e]{1,3}",
    r"sini+i+",
    r"ay+o+",
    r"y+u+k+",
    r"kuy+",
    r"mn\s*yg",
    r"ada\s*yang",
    r"siapa\s*mau",
    r"mau\s*ga",

    # =========================
    # BAIT
    # =========================
    r"lagi\s*sendiri",
    r"sendirian\s*nih",
    r"baru\s*putus",
    r"ga\s*bisa\s*tidur",
    r"butuh\s*perhatian",
    r"cari\s*(teman|cwo|cwk)",
    r"yang\s*di\s*jkt",
    r"jkt\s*ada",
]

# =========================================================
# NORMALIZATION
# =========================================================

REPLACE_MAP = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
    "!": "i",
    "|": "i",
}


def remove_invisible(text: str) -> str:
    return "".join(
        c for c in (text or "")
        if unicodedata.category(c)[0] != "C"
    )


def normalize_text(text: str) -> str:
    text = remove_invisible(text)
    text = unicodedata.normalize("NFKD", text).lower()
    text = unidecode(text)

    for old, new in REPLACE_MAP.items():
        text = text.replace(old, new)

    text = re.sub(r"(.)\1{2,}", r"\1", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", normalize_text(text))


def similarity(a: str, b: str) -> float:
    if levenshtein_distance:
        max_len = max(len(a), len(b))
        if max_len == 0:
            return 1.0
        return 1 - (levenshtein_distance(a, b) / max_len)

    return difflib.SequenceMatcher(None, a, b).ratio()


# =========================================================
# DATABASE HELPERS
# =========================================================

async def set_antibc(chat_id: int, status: bool):
    await db.cache.update_one(
        {"_id": f"antibc:{chat_id}"},
        {"$set": {"status": status}},
        upsert=True
    )


async def get_antibc(chat_id: int) -> bool:
    data = await db.cache.find_one({"_id": f"antibc:{chat_id}"})
    return bool(data and data.get("status"))


# =========================================================
# ANKES CHECK
# =========================================================

async def ankes_active(chat_id: int) -> bool:
    try:
        if hasattr(db, "is_ankes"):
            status = await db.is_ankes(chat_id)
            if not status:
                return False

        if hasattr(db, "get_expired"):
            expired = await db.get_expired(chat_id)
            if expired and int(time.time()) > int(expired):
                if hasattr(db, "remove_ankes"):
                    await db.remove_ankes(chat_id)
                return False

        return True
    except Exception:
        return True


# =========================================================
# WHITELIST
# =========================================================

async def is_whitelisted(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    if user_id in SUDO_USERS:
        return True
    return False


async def is_admin(chat_id: int, user_id: int) -> bool:
    if await is_whitelisted(user_id):
        return True

    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
        )
    except Exception:
        return False


# =========================================================
# HARD DETECTION
# =========================================================

def hard_detect(text: str):
    normalized = normalize_text(text)
    compact = compact_text(text)

    for kw in HARD_BLACKLIST:
        if compact_text(kw) in compact:
            return kw

    for pattern in REGEX_PATTERNS:
        if re.search(pattern, normalized):
            return pattern

    if re.search(r"(https?://|t\.me/|telegram\.me|wa\.me)", text.lower()):
        return "link"

    if re.search(r"@\w{4,}", text):
        return "mention"

    return None


# =========================================================
# OPENAI DETECTION
# =========================================================

async def ai_detect(text: str) -> bool:
    if not OPENAI_API_KEY or not text:
        return False

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Kamu adalah AI anti spam Telegram.\n"
                    "Jawab hanya SPAM atau HAM.\n"
                    "SPAM jika pesan mengandung:\n"
                    "- ranah 18+\n"
                    "- ajakan open pc\n"
                    "- promosi\n"
                    "- broadcast\n"
                    "- ajakan dm/pc/chat\n"
                    "- ajakan cek bio\n"
                    "- flirting seksual\n"
                    "- need abang / need partner\n"
                )
            },
            {
                "role": "user",
                "content": text[:3000]
            }
        ],
        "temperature": 0,
        "max_tokens": 5
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        timeout = aiohttp.ClientTimeout(total=15)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                OPENAI_API_URL,
                headers=headers,
                json=payload
            ) as resp:
                if resp.status != 200:
                    print(f"[ANTIBC] AI HTTP {resp.status}")
                    return False

                data = await resp.json()

                result = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                    .upper()
                )

                print(f"[ANTIBC] AI Result: {result}")

                return "SPAM" in result

    except Exception as e:
        print(f"[ANTIBC] AI error: {e}")
        return False


# =========================================================
# ACTION
# =========================================================
async def punish_user(message: Message, reason: str):
    try:
        await message.delete()
        print(f"[ANTIBC] Deleted => {reason}")
    except Exception as e:
        print(f"[ANTIBC] Delete failed: {e}")
        return

    # Mapping reason ke pesan yang lebih jelas
    if reason == "Extra Antispam Detection":
        warn_text = (
            "⚠️ Spam terdeteksi dan dihapus.\n"
            "Reason: Extra Antispam Detection"
        )
    elif reason.startswith("Hard Blacklist"):
        warn_text = (
            "⚠️ Pesan mengandung kata terlarang.\n"
            f"Reason: {reason}"
        )
    elif reason == "AI Detection":
        warn_text = (
            "⚠️ AI mendeteksi pesan sebagai spam.\n"
            "Reason: AI Detection"
        )
    elif reason == "Forward Message":
        warn_text = (
            "⚠️ Pesan forward terdeteksi sebagai broadcast.\n"
            "Reason: Forward Message"
        )
    elif reason == "Repeated Broadcast":
        warn_text = (
            "⚠️ Pesan berulang terdeteksi.\n"
            "Reason: Repeated Broadcast"
        )
    elif reason == "Similar Broadcast":
        warn_text = (
            "⚠️ Pesan mirip berulang terdeteksi.\n"
            "Reason: Similar Broadcast"
        )
    elif reason == "Cross Group Broadcast":
        warn_text = (
            "⚠️ Broadcast lintas grup terdeteksi.\n"
            "Reason: Cross Group Broadcast"
        )
    elif reason == "Fast Flood":
        warn_text = (
            "⚠️ Flood message terdeteksi.\n"
            "Reason: Fast Flood"
        )
    else:
        warn_text = (
            "⚠️ Spam terdeteksi dan dihapus.\n"
            f"Reason: {reason}"
        )

    try:
        warn = await app.send_message(
            message.chat.id,
            warn_text
        )
        print(f"[ANTIBC] Warning sent => {reason}")
        await asyncio.sleep(4)
        await warn.delete()
    except Exception as e:
        print(f"[ANTIBC] Warning send failed: {e}")


# =========================================================
# COMMAND
# =========================================================
@app.on_message(filters.command("antibc") & filters.group)
async def antibc_toggle(_, message: Message):
    if not message.from_user:
        return

    # Hanya admin / owner / sudo yang boleh
    if not await is_admin(
        message.chat.id,
        message.from_user.id
    ):
        return

    # Format command
    if len(message.command) < 2:
        return await message.reply_text(
            "Gunakan:\n"
            "/antibc on\n"
            "/antibc off"
        )

    arg = message.command[1].lower()

    # Aktifkan antibroadcast
    if arg == "on":
        await set_antibc(
            message.chat.id,
            True
        )
        await message.reply_text(
            "✅ AntiBroadcast aktif."
        )

    # Nonaktifkan antibroadcast
    elif arg == "off":
        await set_antibc(
            message.chat.id,
            False
        )
        await message.reply_text(
            "✅ AntiBroadcast nonaktif."
        )

    # Argumen salah
    else:
        await message.reply_text(
            "Gunakan:\n"
            "/antibc on\n"
            "/antibc off"
        )


# =========================================================
# =========================================================
# MAIN
# =========================================================

@app.on_message(filters.group & ~filters.service, group=-20)
async def antibroadcast_main(_, message: Message):
    try:
        if not message or not message.from_user:
            return

        chat_id = message.chat.id
        user_id = message.from_user.id

        print(f"[ANTIBC] New message from {user_id} in {chat_id}")

        # antibc aktif?
        if not await get_antibc(chat_id):
            print("[ANTIBC] Disabled")
            return

        # ankes aktif?
        if not await ankes_active(chat_id):
            print("[ANTIBC] Ankes inactive")
            return

        # admin / owner / sudo skip
        if await is_admin(chat_id, user_id):
            print("[ANTIBC] User is admin")
            return

        # =====================================================
        # KUMPULKAN TEKS
        # =====================================================
        text_parts = []

        if message.text:
            text_parts.append(message.text)

        if message.caption:
            text_parts.append(message.caption)

        user = message.from_user

        if user.first_name:
            text_parts.append(user.first_name)

        if user.last_name:
            text_parts.append(user.last_name)

        if user.username:
            text_parts.append(user.username)

        # NOTE:
        # app.get_users() cukup berat.
        # Hanya ambil bio jika pesan cukup panjang.
        try:
            if message.text and len(message.text) >= 15:
                full_user = await app.get_users(user_id)

                if getattr(full_user, "bio", None):
                    text_parts.append(full_user.bio)
                elif getattr(full_user, "about", None):
                    text_parts.append(full_user.about)
        except Exception:
            pass

        text_raw = "\n".join(str(x) for x in text_parts if x).strip()

        print(f"[ANTIBC] Full text: {text_raw}")

        if not text_raw and not message.forward_date:
            return

        compact = compact_text(text_raw)

        if len(compact) < 2 and not message.forward_date:
            return

        now = time.time()
        user_key = str(user_id)

        # =====================================================
        # DATABASE BLACKLIST CHECK
        # =====================================================
        try:
            blacklist_words = await db.get_blacklist(chat_id)

            if blacklist_words:
                for word in blacklist_words:
                    if not word:
                        continue

                    db_word = compact_text(str(word))

                    # Match langsung
                    if db_word and db_word in compact:
                        print(f"[ANTIBC] DB BLACKLIST => {word}")
                        await punish_user(
                            message,
                            f"Blacklist DB: {word}"
                        )
                        return

                    # Similar typo
                    if (
                        db_word
                        and len(db_word) >= 3
                        and similarity(db_word, compact) >= 0.85
                    ):
                        print(
                            f"[ANTIBC] DB BLACKLIST SIMILAR => {word}"
                        )
                        await punish_user(
                            message,
                            f"Blacklist DB Similar: {word}"
                        )
                        return

        except Exception as e:
            print(f"[ANTIBC] DB blacklist error: {e}")

        # =====================================================
        # EXTRA ANTISPAM DETECTION
        # =====================================================
        try:
            extra_reason = extra_detect(text_raw, user_id)

            if extra_reason:
                print(f"[ANTIBC] EXTRA DETECT => {extra_reason}")
                await punish_user(
                    message,
                    "Extra Antispam Detection"
                )
                return

        except Exception as e:
            print(f"[ANTIBC] Extra detect error: {e}")

        # =====================================================
        # HARD DETECT
        # =====================================================
        reason = hard_detect(text_raw)

        if reason:
            print(f"[ANTIBC] HARD DETECT => {reason}")
            await punish_user(
                message,
                f"Hard Blacklist: {reason}"
            )
            return

        # =====================================================
        # FORWARD DETECT
        # =====================================================
        if message.forward_date:
            await punish_user(message, "Forward Message")
            return

        # =====================================================
        # AI DETECT
        # HANYA JIKA ADA KATA MENCURIGAKAN
        # =====================================================
        suspicious_words = [
            "need", "open", "dm", "pc", "chat",
            "vcs", "bo", "biyoh", "bokep",
            "premium", "vip", "gabut", "bosen",
            "temenin", "call", "lucu", "ganteng",
            "cari", "partner"
        ]

        if any(word in compact for word in suspicious_words):
            print("[ANTIBC] Checking AI...")

            if await ai_detect(text_raw):
                await punish_user(message, "AI Detection")
                return

        # =====================================================
        # CACHE CHECK
        # =====================================================
        async with LOCKS[user_key]:

            # ---------------- Fast Flood ----------------
            fast = USER_FAST_CACHE[user_key]
            fast.append(now)

            fast_count = sum(
                1 for ts in fast
                if now - ts <= FAST_MESSAGE_WINDOW
            )

            if fast_count >= FAST_MESSAGE_LIMIT:
                await punish_user(message, "Fast Flood")
                return

            # ---------------- Repeat ----------------
            cache = USER_MESSAGE_CACHE[user_key]
            cache.append({
                "text": compact,
                "time": now,
                "chat": chat_id,
            })

            same_count = sum(
                1 for x in cache
                if x["text"] == compact
                and now - x["time"] <= REPEAT_WINDOW
            )

            if same_count >= REPEAT_LIMIT:
                await punish_user(
                    message,
                    "Repeated Broadcast"
                )
                return

            # ---------------- Similar ----------------
            similar_count = 0

            for x in cache:
                if now - x["time"] > SIMILAR_WINDOW:
                    continue

                if similarity(x["text"], compact) >= 0.80:
                    similar_count += 1

            if similar_count >= SIMILAR_LIMIT:
                await punish_user(
                    message,
                    "Similar Broadcast"
                )
                return

            # ---------------- Cross Group ----------------
            cross = USER_CROSS_CACHE[user_key]
            cross.append({
                "text": compact,
                "chat": chat_id,
                "time": now,
            })

            groups = set()

            for x in cross:
                if now - x["time"] > CROSS_GROUP_WINDOW:
                    continue

                if similarity(x["text"], compact) >= 0.80:
                    groups.add(x["chat"])

            if len(groups) >= CROSS_GROUP_LIMIT:
                await punish_user(
                    message,
                    "Cross Group Broadcast"
                )
                return

            # ---------------- Duplicate Same Chat ----------------
            last_key = str(chat_id)

            if LAST_CHAT_MESSAGE.get(last_key) == compact:
                await punish_user(
                    message,
                    "Duplicate Message"
                )
                return

            LAST_CHAT_MESSAGE[last_key] = compact

    except Exception as e:
        print(f"[ANTIBC] ERROR: {e}")
