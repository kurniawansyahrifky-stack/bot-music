# Copyright (c) 2025 AnonymousX1025

import math
import requests

from pyrogram import filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from anony import app

translate_db = {}

LANGUAGES = {
    "en": "🇺🇸 Eng", "id": "🇮🇩 Indo", "ja": "🇯🇵 Jpn", "zh-CN": "🇨🇳 Chn",
    "ko": "🇰🇷 Kor", "ru": "🇷🇺 Rus", "ar": "🇸🇦 Arb", "fr": "🇫🇷 Fr",
    "de": "🇩🇪 Ger", "es": "🇪🇸 Spn", "it": "🇮🇹 Ita", "pt": "🇵🇹 Prt",
    "nl": "🇳🇱 Dut", "tr": "🇹🇷 Trk", "hi": "🇮🇳 Hin", "th": "🇹🇭 Thai",
    "vi": "🇻🇳 Vie", "uk": "🇺🇦 Ukr", "pl": "🇵🇱 Pol", "ms": "🇲🇾 Mly",
    "bn": "🇧🇩 Ben", "fa": "🇮🇷 Per", "ur": "🇵🇰 Urd", "ta": "🇮🇳 Tam",
    "te": "🇮🇳 Tel", "ml": "🇮🇳 Mal", "mr": "🇮🇳 Mar", "gu": "🇮🇳 Guj",
    "pa": "🇮🇳 Pun", "sw": "🇰🇪 Swa", "fil": "🇵🇭 Fil", "ro": "🇷🇴 Rom",
    "hu": "🇭🇺 Hun", "el": "🇬🇷 Grk", "cs": "🇨🇿 Cze", "sk": "🇸🇰 Slk",
    "da": "🇩🇰 Dan", "fi": "🇫🇮 Fin", "no": "🇳🇴 Nor", "sv": "🇸🇪 Swe",
    "he": "🇮🇱 Heb", "sr": "🇷🇸 Srb", "hr": "🇭🇷 Cro", "bg": "🇧🇬 Bul",
    "jw": "🇮🇩 Jav", "su": "🇮🇩 Sun", "af": "🇿🇦 Afr", "sq": "🇦🇱 Alb"
}

LANG_ITEMS = list(LANGUAGES.items())
PER_PAGE = 16


def google_translate(text, target):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target,
        "dt": "t",
        "q": text
    }
    response = requests.get(url, params=params).json()
    return "".join([i[0] for i in response[0]])


def build_buttons(user_id, page=0):
    rows = []
    start = page * PER_PAGE
    end = start + PER_PAGE
    chunk = LANG_ITEMS[start:end]

    temp = []
    for code, name in chunk:
        temp.append(InlineKeyboardButton(name, callback_data=f"tr|{code}|{user_id}"))

        if len(temp) == 4:
            rows.append(temp)
            temp = []

    if temp:
        rows.append(temp)

    total_pages = math.ceil(len(LANG_ITEMS) / PER_PAGE)

    nav = []

    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page|{page-1}|{user_id}"))

    nav.append(InlineKeyboardButton("❌ Cancel", callback_data=f"close|{user_id}"))

    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"page|{page+1}|{user_id}"))

    rows.append(nav)

    return InlineKeyboardMarkup(rows)


# ================================
# COMMAND /translate
# ================================

@app.on_message(filters.command("translate"))
async def translate_menu(_, message: Message):

    if not message.reply_to_message:
        return await message.reply_text("Reply pesan yang mau ditranslate.")

    text = message.reply_to_message.text or message.reply_to_message.caption

    if not text:
        return await message.reply_text("Tidak ada text.")

    user_id = message.from_user.id
    translate_db[user_id] = text

    await message.reply_text(
        "🌐 Select Translation Language",
        reply_markup=build_buttons(user_id, 0)
    )


# ================================
# CALLBACK PAGE
# ================================

@app.on_callback_query(filters.regex("^page\\|"))
async def change_page(_, query: CallbackQuery):

    _, page, owner_id = query.data.split("|")
    page = int(page)
    owner_id = int(owner_id)

    if query.from_user.id != owner_id:
        return await query.answer("Ini bukan tombol kamu.", show_alert=True)

    await query.message.edit_reply_markup(build_buttons(owner_id, page))


# ================================
# CALLBACK TRANSLATE
# ================================

@app.on_callback_query(filters.regex("^tr\\|"))
async def translate_callback(_, query: CallbackQuery):

    _, lang, owner_id = query.data.split("|")
    owner_id = int(owner_id)

    if query.from_user.id != owner_id:
        return await query.answer("Ini bukan tombol kamu.", show_alert=True)

    if owner_id not in translate_db:
        return await query.answer("Text expired.", show_alert=True)

    text = translate_db[owner_id]

    try:
        hasil = google_translate(text, lang)
        await query.message.edit_text(hasil)
        del translate_db[owner_id]
    except Exception as e:
        await query.message.edit_text(f"Gagal translate\n{e}")


# ================================
# CALLBACK CLOSE
# ================================

@app.on_callback_query(filters.regex("^close\\|"))
async def close_translate(_, query: CallbackQuery):

    _, owner_id = query.data.split("|")
    owner_id = int(owner_id)

    if query.from_user.id != owner_id:
        return await query.answer("Ini bukan tombol kamu.", show_alert=True)

    await query.message.delete()

    if owner_id in translate_db:
        del translate_db[owner_id]
