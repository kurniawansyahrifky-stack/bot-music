# anony/plugins/lyrics.py

import aiohttp
from pyrogram import filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from anony import app

# Cache sementara untuk pagination
lyrics_cache = {}


# =========================================================
# SEARCH LYRICS FROM LRCLIB (FREE API, NO TOKEN NEEDED)
# =========================================================
async def search_lyrics(query: str):
    url = "https://lrclib.net/api/search"
    params = {"q": query}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=15) as resp:
            if resp.status != 200:
                return []

            data = await resp.json()
            return data


# =========================================================
# SPLIT LONG TEXT
# =========================================================
def split_text(text, limit=3500):
    return [text[i:i + limit] for i in range(0, len(text), limit)]


# =========================================================
# /LIRIK COMMAND
# =========================================================
@app.on_message(filters.command(["lirik", "lyrics"]))
async def lyrics_command(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "🎵 <b>Cara penggunaan:</b>\n"
            "<code>/lirik Noah Separuh Aku</code>"
        )

    query = " ".join(message.command[1:])

    searching = await message.reply_text(
        f"🔍 <b>Mencari lirik...</b>\n"
        f"🎵 <code>{query}</code>"
    )

    try:
        results = await search_lyrics(query)

        if not results:
            return await searching.edit_text(
                "❌ Lirik tidak ditemukan."
            )

        # Ambil hasil pertama
        song = results[0]

        title = song.get("trackName", "Unknown")
        artist = song.get("artistName", "Unknown")
        album = song.get("albumName", "-")
        lyrics = song.get("plainLyrics")

        if not lyrics:
            return await searching.edit_text(
                "❌ Lirik tidak tersedia."
            )

        pages = split_text(lyrics)

        cache_id = f"{message.from_user.id}_{message.id}"

        lyrics_cache[cache_id] = {
            "pages": pages,
            "title": title,
            "artist": artist,
            "album": album,
        }

        header = (
            f"🎵 <b>{title}</b>\n"
            f"👤 <b>{artist}</b>\n"
            f"💿 <b>{album}</b>\n\n"
        )

        text = header + pages[0]

        buttons = []

        if len(pages) > 1:
            buttons.append([
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data=f"lyrics_next|{cache_id}|0"
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                "❌ Close",
                callback_data=f"lyrics_close|{cache_id}"
            )
        ])

        await searching.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        await searching.edit_text(
            f"❌ <b>Terjadi error saat mengambil lirik.</b>\n\n"
            f"<code>{e}</code>"
        )


# =========================================================
# CALLBACK BUTTONS
# =========================================================
@app.on_callback_query(filters.regex(r"^lyrics_"))
async def lyrics_callback(_, query: CallbackQuery):
    try:
        data = query.data.split("|")
        action = data[0]

        # Close button
        if action == "lyrics_close":
            await query.message.delete()
            return

        cache_id = data[1]
        current_index = int(data[2])

        # Hanya user yang menjalankan command yang boleh klik
        owner_id = int(cache_id.split("_")[0])
        if not query.from_user or query.from_user.id != owner_id:
            return await query.answer(
                "❌ Ini bukan milik kamu.",
                show_alert=True
            )

        if cache_id not in lyrics_cache:
            return await query.answer(
                "❌ Data lirik sudah expired.",
                show_alert=True
            )

        cache = lyrics_cache[cache_id]
        pages = cache["pages"]

        if action == "lyrics_next":
            new_index = current_index + 1
        elif action == "lyrics_prev":
            new_index = current_index - 1
        else:
            return

        new_index = max(0, min(new_index, len(pages) - 1))

        header = (
            f"🎵 <b>{cache['title']}</b>\n"
            f"👤 <b>{cache['artist']}</b>\n"
            f"💿 <b>{cache['album']}</b>\n"
            f"📄 <b>Page {new_index + 1}/{len(pages)}</b>\n\n"
        )

        text = header + pages[new_index]

        buttons = []
        nav = []

        if new_index > 0:
            nav.append(
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data=f"lyrics_prev|{cache_id}|{new_index}"
                )
            )

        if new_index < len(pages) - 1:
            nav.append(
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data=f"lyrics_next|{cache_id}|{new_index}"
                )
            )

        if nav:
            buttons.append(nav)

        buttons.append([
            InlineKeyboardButton(
                "❌ Close",
                callback_data=f"lyrics_close|{cache_id}"
            )
        ])

        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

        await query.answer()

    except Exception as e:
        await query.answer(
            f"Error: {e}",
            show_alert=True
        )
