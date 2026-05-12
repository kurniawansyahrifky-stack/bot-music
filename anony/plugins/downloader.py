# GARFIELD UNIVERSAL MONSTER DOWNLOADER + TELEGRAM BYPASS + VC PLAYER + SOCIAL MEDIA RESOLVER

import os
import re
import yt_dlp
import time
import asyncio
import contextlib
from pathlib import Path

from pyrogram import filters, types
from pyrogram.errors import FloodWait
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from anony import app, config, queue, anon, tg, yt, db, userbot

DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

TEMP_DL = {}
SOCIAL_DOMAINS = [
    "youtube.com", "youtu.be",
    "instagram.com",
    "tiktok.com",
    "facebook.com", "fb.watch",
    "twitter.com", "x.com",
    "pinterest.com",
    "threads.net",
    "spotify.com",
    "t.me"
]


# =====================================================
# URL VALIDATOR
# =====================================================

def is_valid_url(url):
    regex = re.compile(
        r'^(https?://)?'
        r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,}|t\.me)'
        r'(/[A-Za-z0-9._~:/?#@!$&\'()*+,;=%+-]*)?$'
    )
    return re.match(regex, url)


def detect_source_name(url):
    txt = url.lower()

    if "youtube" in txt or "youtu.be" in txt:
        return "YouTube"
    elif "instagram" in txt:
        return "Instagram"
    elif "tiktok" in txt:
        return "TikTok"
    elif "facebook" in txt or "fb.watch" in txt:
        return "Facebook"
    elif "twitter" in txt or "x.com" in txt:
        return "Twitter/X"
    elif "pinterest" in txt:
        return "Pinterest"
    elif "threads.net" in txt:
        return "Threads"
    elif "spotify" in txt:
        return "Spotify"
    elif "t.me" in txt:
        return "Telegram"
    return "Universal Media"


# =====================================================
# LOGGER
# =====================================================

async def send_dl_log(text):
    try:
        await app.send_message(config.LOG_GROUP_ID, text)
    except:
        pass


# =====================================================
# BUTTON UI
# =====================================================

def dl_buttons(key):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎵 AUDIO PLAY", callback_data=f"gdl_audio|{key}"),
                InlineKeyboardButton("🎬 VIDEO PLAY", callback_data=f"gdl_video|{key}")
            ],
            [
                InlineKeyboardButton("📦 DOWNLOAD FILE", callback_data=f"gdl_file|{key}")
            ],
            [
                InlineKeyboardButton("🗑 CANCEL", callback_data=f"gdl_cancel|{key}")
            ]
        ]
    )


# =====================================================
# COMMAND HANDLER
# =====================================================

@app.on_message(filters.command("dl") & ~app.bl_users)
async def smart_downloader(_, message: types.Message):
    source = None
    source_type = None
    source_name = None

    if len(message.command) >= 2:
        source = message.command[1].strip()
        source_type = "url"
        source_name = detect_source_name(source)

    elif message.reply_to_message:
        rep = message.reply_to_message

        if rep.text and is_valid_url(rep.text.strip()):
            source = rep.text.strip()
            source_type = "url"
            source_name = detect_source_name(source)

        elif rep.caption and is_valid_url(rep.caption.strip()):
            source = rep.caption.strip()
            source_type = "url"
            source_name = detect_source_name(source)

        else:
            media = tg.get_media(rep)
            if media:
                source = rep
                source_type = "telegram_media"
                source_name = "Telegram Media"

    if not source:
        return await message.reply_text(
            "**📥 GARFIELD UNIVERSAL DOWNLOADER**\n"
            "━━━━━━━━━━━━━━\n"
            "Usage : `/dl link`\n"
            "or reply media/link with `/dl`\n\n"
            "**Supported Sources**\n"
            "★ YouTube / Shorts\n"
            "★ Instagram / Reels\n"
            "★ TikTok / Facebook\n"
            "★ Twitter / Pinterest / Threads\n"
            "★ Spotify Preview\n"
            "★ Telegram Channel Post\n"
            "★ Telegram Replied Media",
            quote=True
        )

    key = f"{message.chat.id}_{message.id}_{int(time.time())}"

    TEMP_DL[key] = {
        "source": source,
        "type": source_type,
        "user": message.from_user.id,
        "name": source_name
    }

    await message.reply_text(
        f"**📥 GARFIELD SMART RESOLVER**\n"
        f"━━━━━━━━━━━━━━\n"
        f"★ Source : `{source_name}`\n"
        f"★ Media Detected Successfully\n"
        f"★ Select Action Below",
        reply_markup=dl_buttons(key),
        quote=True
    )


# =====================================================
# YTDLP URL PROCESSOR
# =====================================================

async def process_url_download(url, video=False, audio=False):
    ydl_opts = {
        "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
        "quiet": True,
        "nocheckcertificate": True,
        "noplaylist": True,
        "geo_bypass": True,
        "cookiefile": None
    }

    if audio:
        ydl_opts["format"] = "bestaudio/best"
    elif video:
        ydl_opts["format"] = "bestvideo+bestaudio/best"
        ydl_opts["merge_output_format"] = "mp4"
    else:
        ydl_opts["format"] = "best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

        title = info.get("title", "Unknown")
        duration = info.get("duration", 0)
        uploader = info.get("uploader", "Unknown")

        return info, file_path, title, duration, uploader


# =====================================================
# TELEGRAM LINK PROCESSOR
# =====================================================

async def process_tg_link(link):
    return await userbot.download_tg_post(link)


# =====================================================
# SEND FILE TO USER
# =====================================================

async def send_downloaded_file(msg, path):
    if path.endswith((".mp3", ".m4a", ".wav", ".ogg")):
        await msg.reply_audio(audio=path, caption="📦 GARFIELD DOWNLOADER ✓")

    elif path.endswith((".jpg", ".jpeg", ".png", ".webp")):
        await msg.reply_photo(photo=path, caption="📦 GARFIELD DOWNLOADER ✓")

    elif path.endswith((".mp4", ".mkv", ".mov", ".webm", ".gif")):
        await msg.reply_video(video=path, caption="📦 GARFIELD DOWNLOADER ✓")

    else:
        await msg.reply_document(document=path, caption="📦 GARFIELD DOWNLOADER ✓")


# =====================================================
# CALLBACK HANDLER
# =====================================================

@app.on_callback_query(filters.regex("^gdl_"))
async def gdl_callback(_, cq: CallbackQuery):
    data = cq.data.split("|")
    action = data[0]
    key = data[1]

    if key not in TEMP_DL:
        return await cq.answer("Session Expired", show_alert=True)

    cache = TEMP_DL[key]

    if cq.from_user.id != cache["user"]:
        return await cq.answer("This panel is not yours.", show_alert=True)

    source = cache["source"]
    stype = cache["type"]
    sname = cache["name"]

    await cq.message.edit_text(
        f"**⚙ GARFIELD ENGINE PROCESSING**\n"
        f"━━━━━━━━━━━━━━\n"
        f"★ Resolving : `{sname}`\n"
        f"★ Please Wait..."
    )

    file_path = None

    try:

        # ================================= AUDIO PLAY
        if action == "gdl_audio":

            if stype == "telegram_media":
                file = await tg.download(source, cq.message)
                file.user = cq.from_user.mention

            elif "t.me/" in str(source):
                path, msg = await process_tg_link(source)
                file = await tg.download(msg, cq.message)
                file.user = cq.from_user.mention

            else:
                info, file_path, title, duration, uploader = await process_url_download(source, audio=True)
                file = await yt.search(source, cq.message.id, video=False)
                file.file_path = file_path
                file.user = cq.from_user.mention

            pos = queue.add(cq.message.chat.id, file)

            if pos == 0 and not await db.get_call(cq.message.chat.id):
                await anon.play_media(cq.message.chat.id, cq.message, file)
                await cq.message.edit_text("🎵 Audio Added To VC & Now Playing ✓")
            else:
                await cq.message.edit_text(f"🎵 Audio Queued At Position {pos} ✓")

            await send_dl_log(
                f"🎵 GARFIELD AUDIO PLAY\n"
                f"User : {cq.from_user.mention}\n"
                f"Source : {source}\n"
                f"Resolver : {sname}\n"
                f"Status : SUCCESS"
            )

        # ================================= VIDEO PLAY
        elif action == "gdl_video":

            if stype == "telegram_media":
                file = await tg.download(source, cq.message)
                file.user = cq.from_user.mention

            elif "t.me/" in str(source):
                path, msg = await process_tg_link(source)
                file = await tg.download(msg, cq.message)
                file.user = cq.from_user.mention

            else:
                info, file_path, title, duration, uploader = await process_url_download(source, video=True)
                file = await yt.search(source, cq.message.id, video=True)
                file.file_path = file_path
                file.user = cq.from_user.mention

            pos = queue.add(cq.message.chat.id, file)

            if pos == 0 and not await db.get_call(cq.message.chat.id):
                await anon.play_media(cq.message.chat.id, cq.message, file)
                await cq.message.edit_text("🎬 Video Added To VC & Streaming ✓")
            else:
                await cq.message.edit_text(f"🎬 Video Queued At Position {pos} ✓")

            await send_dl_log(
                f"🎬 GARFIELD VIDEO PLAY\n"
                f"User : {cq.from_user.mention}\n"
                f"Source : {source}\n"
                f"Resolver : {sname}\n"
                f"Status : SUCCESS"
            )

        # ================================= FILE MODE
        elif action == "gdl_file":

            if stype == "telegram_media":
                path = await app.download_media(source)

            elif "t.me/" in str(source):
                path, msg = await process_tg_link(source)

            else:
                info, path, title, duration, uploader = await process_url_download(source)

            await send_downloaded_file(cq.message, path)
            await cq.message.delete()

            await send_dl_log(
                f"📦 GARFIELD FILE DOWNLOAD\n"
                f"User : {cq.from_user.mention}\n"
                f"Source : {source}\n"
                f"Resolver : {sname}\n"
                f"Status : SUCCESS"
            )

            with contextlib.suppress(Exception):
                os.remove(path)

        # ================================= CANCEL
        elif action == "gdl_cancel":
            await cq.message.delete()

    except FloodWait as e:
        await asyncio.sleep(e.value)

    except Exception as e:
        await send_dl_log(
            f"⚠ GARFIELD DOWNLOADER ERROR\n"
            f"User : {cq.from_user.mention}\n"
            f"Source : {source}\n"
            f"Resolver : {sname}\n"
            f"Error : {str(e)}"
        )
        await cq.message.edit_text(f"❌ Process Failed\n\n`{e}`")

    finally:
        if file_path:
            with contextlib.suppress(Exception):
                if Path(file_path).exists():
                    os.remove(file_path)

        if key in TEMP_DL:
            del TEMP_DL[key]
