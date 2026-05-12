# anony/plugins/antispam.py

import re
import time
import asyncio
import unicodedata
import difflib

from collections import defaultdict, deque

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from anony import app, db, config

# =========================================================
# CACHE
# =========================================================

SPAM_CACHE = {}
BLACKLIST_CACHE = {}
WHITELIST_CACHE = {}
ADMIN_CACHE = {}
MESSAGE_CACHE = {}
MEDIA_CACHE = {}

USER_MESSAGES = defaultdict(lambda: deque(maxlen=20))
USER_HISTORY = defaultdict(lambda: deque(maxlen=15))
USER_LINKS = defaultdict(lambda: deque(maxlen=10))
USER_EMOJIS = defaultdict(lambda: deque(maxlen=10))
USER_CAPS = defaultdict(lambda: deque(maxlen=10))

# =========================================================
# SETTINGS
# =========================================================

FLOOD_LIMIT = 4
FLOOD_TIME = 5

REPEAT_LIMIT = 4
REPEAT_TIME = 15

SIMILAR_LIMIT = 3
SIMILAR_PERCENT = 0.67

EMOJI_LIMIT = 4

CAPS_LIMIT = 30

LINK_LIMIT = 2

LONG_TEXT_LIMIT = 25

SYMBOL_LIMIT = 13

FORWARD_LIMIT = 4

MENTION_LIMIT = 3

USERNAME_LIMIT = 5

# =========================================================
# OWNER / SUDO
# =========================================================

OWNER = config.OWNER_ID

SUDO = []

try:
    if isinstance(config.SUDO_USERS, list):
        SUDO = config.SUDO_USERS
except:
    pass

# =========================================================
# BAD WORDS
# =========================================================

BAD_WORDS = [

    # BASIC
    "kontol",
    "kntl",
    "mmk",
    "memek",
    "meki",
    "ngentot",
    "ngntt",
    "ngewe",
    "ngew",
    "coli",
    "ngocok",
    "bokep",
    "sange",
    "horny",
    "sex",
    "seks",
    "sexx",
    "s3x",
    "s*x",
    "vcs",
    "vc sex",
    "open vc",
    "open vcs",
    "pap",
    "pap tt",
    "pap ngentot",
    "pap bugil",
    "pap vcs",
    "pap memek",
    "pap kontol",
    "bugil",
    "toket",
    "tetek",
    "pepek",
    "tempik",
    "jembut",
    "bispak",
    "lonte",
    "bo",
    "openbo",
    "open bo",

    # VIP / JUALAN
    "vv1p",
    "v1p",
    "vip",
    "vip murah",
    "vip grup",
    "jual akun",
    "ahat",
    "jajan",
    "media save",
    "murah",
    "panel privat",
    "suntik sosmed",
    "open jasa",
    "nokos",
    "nokos wa",
    "jasa unban",
    "fwbeh",
    "Tmoh",
    "Tbyt",
    "promosi",

    # BYPASS
    "by0h",
    "byoh",
    "t.me",
    "telegr4m",
    "callsex",
    "smean",
    "crot",
    "crotin",

    # HORNY
    "desah",
    "cewe sange",
    "cowo sange",
    "ngocok bareng",
    "coli bareng",
    "cari horny",

]

# =========================================================
# REGEX
# =========================================================

LINK_REGEX = re.compile(
    r"(https?:\/\/|t\.me\/|telegram\.me\/|wa\.me\/|chat\.whatsapp\.com|discord\.gg|tinyurl|bit\.ly)",
    re.IGNORECASE,
)

USERNAME_REGEX = re.compile(
    r"@\w+",
    re.IGNORECASE,
)

EMOJI_REGEX = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

FANCY_FONT = re.compile(
    r"[𝔞-𝔷𝕒-𝕫𝐚-𝐳𝓪-𝔃🅐-🅩ⓐ-ⓩ]"
)

# =========================================================
# NORMALIZER
# =========================================================

def normalize_text(text):

    text = text.lower()

    text = unicodedata.normalize("NFKD", text)

    replace_map = {
        "0": "o",
        "1": "i",
        "2": "z",
        "3": "e",
        "4": "a",
        "5": "s",
        "6": "g",
        "7": "t",
        "8": "b",
        "9": "g",
        "@": "a",
        "$": "s",
        "!": "i",
        "|": "i",
        "¥": "y",
        "+": "t",
    }

    for old, new in replace_map.items():
        text = text.replace(old, new)

    text = re.sub(r"(.)\1{2,}", r"\1", text)

    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()

# =========================================================
# HELPERS
# =========================================================

async def delete_message(message):

    try:
        await message.delete()
    except:
        pass


async def spam_notice(
    message: Message,
    text: str = "☠️ TERDETEKSI,Jᴇʟᴇᴋ ᴍᴇɴᴅɪɴɢ ᴀᴘᴜs"
):

    try:

        try:
            await message.delete()
        except:
            pass

        notif = await message.reply_text(
            text,
            quote=False
        )

        await asyncio.sleep(2)

        try:
            await notif.delete()
        except:
            pass

    except:
        pass

async def ankes_active(chat_id):

    status = await db.is_ankes(chat_id)

    if not status:
        return False

    expired = await db.get_expired(chat_id)

    if not expired:
        return False

    now = int(time.time())

    if now > int(expired):

        await db.remove_ankes(chat_id)

        return False

    return True


async def is_admin(chat_id, user_id):

    if user_id == OWNER:
        return True

    if user_id in SUDO:
        return True

    cache_key = f"{chat_id}:{user_id}"

    if cache_key in ADMIN_CACHE:

        cache = ADMIN_CACHE[cache_key]

        if time.time() - cache["time"] <= 120:
            return cache["status"]

    try:

        member = await app.get_chat_member(chat_id, user_id)

        status = member.status in [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ]

        ADMIN_CACHE[cache_key] = {
            "status": status,
            "time": time.time()
        }

        return status

    except:
        return False


async def get_blacklist(chat_id):

    if chat_id in BLACKLIST_CACHE:
        return BLACKLIST_CACHE[chat_id]

    custom = await db.get_blacklist(chat_id)

    merged = list(set(BAD_WORDS + custom))

    BLACKLIST_CACHE[chat_id] = merged

    return merged


async def get_whitelist(chat_id):

    if chat_id in WHITELIST_CACHE:
        return WHITELIST_CACHE[chat_id]

    white = await db.get_whitelist(chat_id)

    WHITELIST_CACHE[chat_id] = white

    return white


def similarity(a, b):

    return difflib.SequenceMatcher(
        None,
        a,
        b
    ).ratio()

# =========================================================
# COMMANDS
# =========================================================

@app.on_message(filters.command("antispam") & filters.group)
async def antispam_toggle(_, message: Message):

    if not message.from_user:
        return

    if not await is_admin(
        message.chat.id,
        message.from_user.id
    ):
        return

    if not await ankes_active(message.chat.id):

        return await message.reply_text(
            "❌ Group tidak memiliki akses ankes."
        )

    if len(message.command) < 2:

        return await message.reply_text(
            "Gunakan:\n/antispam on\n/antispam off"
        )

    arg = message.command[1].lower()

    if arg == "on":

        await db.set_antispam(
            message.chat.id,
            True
        )

        return await message.reply_text(
            "✅ Antispam berhasil diaktifkan."
        )

    elif arg == "off":

        await db.set_antispam(
            message.chat.id,
            False
        )

        return await message.reply_text(
            "✅ Antispam berhasil dimatikan."
        )


# =========================================================
# BLACKLIST
# =========================================================

@app.on_message(filters.command("bl") & filters.group)
async def add_blacklist(_, message: Message):

    if not message.from_user:
        return

    if not await is_admin(
        message.chat.id,
        message.from_user.id
    ):
        return

    word = None

    # kalau reply message
    if message.reply_to_message:

        target = message.reply_to_message

        if target.text:
            word = normalize_text(target.text)

        elif target.caption:
            word = normalize_text(target.caption)

    # kalau manual /bl kata
    elif len(message.command) >= 2:

        word = normalize_text(
            message.text.split(None, 1)[1]
        )

    if not word:

        return await message.reply_text(
            "Gunakan:\n/bl kata\natau reply pesan."
        )

    words = await db.get_blacklist(message.chat.id)

    if word in words:

        return await message.reply_text(
            "❌ Kata sudah ada."
        )

    words.append(word)

    await db.set_blacklist(
        message.chat.id,
        words
    )

    BLACKLIST_CACHE.pop(message.chat.id, None)

    return await message.reply_text(
        f"✅ Blacklist ditambah:\n`{word}`"
    )



@app.on_message(filters.command("unbl") & filters.group)
async def remove_blacklist(_, message: Message):

    if not message.from_user:
        return

    if not await is_admin(
        message.chat.id,
        message.from_user.id
    ):
        return

    if len(message.command) < 2:

        return await message.reply_text(
            "Gunakan:\n/unbl kata"
        )

    word = normalize_text(
        message.text.split(None, 1)[1]
    )

    words = await db.get_blacklist(message.chat.id)

    if word not in words:

        return await message.reply_text(
            "❌ Kata tidak ditemukan."
        )

    words.remove(word)

    await db.set_blacklist(
        message.chat.id,
        words
    )

    BLACKLIST_CACHE.pop(message.chat.id, None)

    return await message.reply_text(
        f"✅ Blacklist dihapus:\n`{word}`"
    )

# =========================================================
# WHITELIST
# =========================================================

@app.on_message(filters.command("addwhite") & filters.group)
async def add_whitelist(_, message: Message):

    if not message.from_user:
        return

    if not await is_admin(
        message.chat.id,
        message.from_user.id
    ):
        return

    if not message.reply_to_message:

        return await message.reply_text(
            "Reply target user."
        )

    user_id = message.reply_to_message.from_user.id

    white = await db.get_whitelist(message.chat.id)

    if user_id in white:

        return await message.reply_text(
            "User sudah whitelist."
        )

    white.append(user_id)

    await db.set_whitelist(
        message.chat.id,
        white
    )

    WHITELIST_CACHE.pop(message.chat.id, None)

    return await message.reply_text(
        "✅ User berhasil di whitelist."
    )


@app.on_message(filters.command("free") & filters.group)
async def remove_whitelist(_, message: Message):

    if not message.from_user:
        return

    if not await is_admin(
        message.chat.id,
        message.from_user.id
    ):
        return

    if not message.reply_to_message:

        return await message.reply_text(
            "Reply target user."
        )

    user_id = message.reply_to_message.from_user.id

    white = await db.get_whitelist(message.chat.id)

    if user_id not in white:

        return await message.reply_text(
            "User tidak whitelist."
        )

    white.remove(user_id)

    await db.set_whitelist(
        message.chat.id,
        white
    )

    WHITELIST_CACHE.pop(message.chat.id, None)

    return await message.reply_text(
        "✅ User berhasil dihapus dari whitelist."
    )


# =========================================================
# MAIN ENGINE
# =========================================================

@app.on_message(
    filters.group &
    ~filters.service,
    group=-1
)
async def antispam_main(_, message: Message):

    try:

        if not message:
            return

        if not message.from_user:
            return

        if not message.chat:
            return

        chat_id = message.chat.id
        user_id = message.from_user.id

        # ============================================
        # CHECK BOT ADMIN
        # ============================================

        try:
            me = await app.get_chat_member(
                chat_id,
                "me"
            )

            if me.status not in [
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER
            ]:
                return

            if not me.privileges.can_delete_messages:
                return

        except:
            return

        # ============================================
        # ANKES CHECK
        # ============================================

        active = await ankes_active(chat_id)

        if not active:
            return

        # ============================================
        # ENABLE CHECK
        # ============================================

        enabled = await db.get_antispam(chat_id)

        if enabled is not True:
            return

        # ============================================
        # ADMIN CHECK
        # ============================================

        if await is_admin(chat_id, user_id):
            return

        # ============================================
        # WHITELIST
        # ============================================

        whitelist = await get_whitelist(chat_id)

        if user_id in whitelist:
            return

        # ============================================
        # TEXT
        # ============================================

        text_raw = ""

        if message.text:
            text_raw = message.text

        elif message.caption:
            text_raw = message.caption

        text = normalize_text(text_raw)

        key = f"{chat_id}:{user_id}"

        now = time.time()

        # ============================================
        # EMPTY
        # ============================================

        if not text_raw:
            text_raw = ""

        # ============================================
        # BLACKLIST
        # ============================================

        blacklist = await get_blacklist(chat_id)

        for word in blacklist:

            if word in text:

                await spam_notice(message)

                return

        # ============================================
        # LINK
        # ============================================

        links = LINK_REGEX.findall(text_raw)

        if len(links) >= LINK_LIMIT:

            await spam_notice(message)

            return

        # ============================================
        # USERNAME FLOOD
        # ============================================

        usernames = USERNAME_REGEX.findall(text_raw)

        if len(usernames) >= USERNAME_LIMIT:

            await spam_notice(message)

            return

        # ============================================
        # EMOJI FLOOD
        # ============================================

        emojis = EMOJI_REGEX.findall(text_raw)

        emoji_count = sum(
            len(x)
            for x in emojis
        )

        if emoji_count >= EMOJI_LIMIT:

            await spam_notice(message)

            return

        # ============================================
        # CAPS FLOOD
        # ============================================

        upper = sum(
            1 for x in text_raw
            if x.isupper()
        )

        total = sum(
            1 for x in text_raw
            if x.isalpha()
        )

        if total > 10:

            percent = (upper / total) * 70

            if percent >= CAPS_LIMIT:

                await spam_notice(message)

                return

        # ============================================
        # LONG TEXT
        # ============================================

        if len(text_raw) >= LONG_TEXT_LIMIT:

            await spam_notice(message)

            return

        # ============================================
        # FANCY FONT
        # ============================================

        if FANCY_FONT.search(text_raw):

            await spam_notice(message)

            return

        # ============================================
        # REPEATED CHAR
        # ============================================

        repeated = re.search(
            r"(.)\1{12,}",
            text_raw
        )

        if repeated:

            await spam_notice(message)

            return

        # ============================================
        # SYMBOL FLOOD
        # ============================================

        weird = re.sub(
            r"[a-zA-Z0-9\s]",
            "",
            text_raw
        )

        if len(weird) >= SYMBOL_LIMIT:

            await spam_notice(message)

            return

        # ============================================
        # FLOOD CACHE
        # ============================================

        spam = SPAM_CACHE.get(key)

        if not spam:

            SPAM_CACHE[key] = {
                "time": now,
                "count": 1
            }

            return

        if now - spam["time"] > FLOOD_TIME:

            SPAM_CACHE[key] = {
                "time": now,
                "count": 1
            }

            return

        spam["count"] += 1

        if spam["count"] >= FLOOD_LIMIT:

            await spam_notice(message)

            return

        # ============================================
        # REPEAT DETECT
        # ============================================

        msg_cache = USER_MESSAGES[key]

        msg_cache.append({
            "text": text,
            "time": now
        })

        same_count = 0

        for data in msg_cache:

            if data["text"] == text:

                if now - data["time"] <= REPEAT_TIME:
                    same_count += 1

        if same_count >= REPEAT_LIMIT:

            await spam_notice(message)

            return

    except Exception as e:
        print(f"ANTISPAM ERROR: {e}")
        return


            
                                
