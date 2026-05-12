import os
import io
import time
import shutil
import zipfile
import asyncio
import traceback
from datetime import datetime

from pyrogram import types
from anony import app, userbot, config


# =========================================================
# CACHE CLEANER
# =========================================================
def cleanup_temp_files():
    folders = [
        "downloads",
        "cache",
        "temp",
        "raw_files",
        ".cache",
    ]

    removed = 0

    for folder in folders:
        if not os.path.exists(folder):
            continue

        for item in os.listdir(folder):
            path = os.path.join(folder, item)

            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)
                removed += 1
            except Exception:
                pass

    return removed


# =========================================================
# STARTUP LOGGER
# =========================================================
async def send_startup_message():
    try:
        # Assistant Started
        try:
            ub = await userbot.clients[0].get_me()
            await app.send_message(
                config.LOG_GROUP,
                f"🎧 <b>{ub.first_name}</b>\nAssistant Started"
            )
        except Exception as e:
            print("assistant startup logger error:", e)

        # Background system notification
        await app.send_message(
            config.LOG_GROUP,
            "✅ Semua sistem background berhasil dijalankan."
        )

        # Cleanup cache/temp files
        removed = cleanup_temp_files()

        await app.send_message(
            config.LOG_GROUP,
            f"🧹 Cache cleaner removed {removed} files."
        )

        # Main startup message
        me = await app.get_me()
        text = (
            "🚀 <b>Bot Running Successfully</b>\n\n"
            f"🤖 <b>Bot:</b> {me.first_name}\n"
            f"🆔 <b>ID:</b> <code>{me.id}</code>\n"
            f"📛 <b>Name:</b> {me.first_name}\n"
            f"🔗 <b>Username:</b> @{me.username}"
        )

        await app.send_message(config.LOG_GROUP, text)

    except Exception as e:
        print("startup logger error:", e)


# =========================================================
# ERROR LOGGER
# =========================================================
async def send_error_log(message, err):
    try:
        chat = message.chat
        user = message.from_user
        tb = traceback.format_exc()

        text = (
            f"❌ <b>Error:</b> {type(err).__name__}\n"
            f"🗓 <b>Date:</b> "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"💬 <b>Chat ID:</b> <code>{chat.id}</code>\n"
            f"📢 <b>Chat Username:</b> "
            f"@{chat.username if chat.username else 'Private'}\n"
            f"👤 <b>User ID:</b> "
            f"<code>{user.id if user else 'Unknown'}</code>\n"
            f"⌨️ <b>Command/Text:</b> "
            f"{message.text or message.caption or '-'}\n\n"
            f"<b>Traceback:</b>\n"
            f"<pre>{tb[:3500]}</pre>"
        )

        await app.send_message(config.LOG_GROUP, text)

    except Exception as e:
        print("send error log failed:", e)


# =========================================================
# CREATE BACKUP
# =========================================================
async def create_backup():
    try:
        name = (
            f"garfasisBot_"
            f"{datetime.now().strftime('%Y-%m-%d_%H%M')}.zip"
        )

        with zipfile.ZipFile(
            name,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zipf:

            excluded = {
                "venv",
                ".venv",
                "__pycache__",
                ".git",
                ".cache",
                "downloads",
                "cache",
                "temp",
                "raw_files",
                "*.log",
            }

            for root, dirs, files in os.walk("."):
                # skip folder yang tidak perlu
                dirs[:] = [
                    d for d in dirs
                    if d not in excluded
                ]

                for file in files:
                    if file.endswith((".log", ".zip")):
                        continue

                    path = os.path.join(root, file)

                    try:
                        zipf.write(path)
                    except Exception:
                        pass

        await app.send_message(
            config.LOG_GROUP,
            "✅ Successfully sent file Backup! "
        )

        await app.send_document(
            config.LOG_GROUP,
            document=name,
            caption=datetime.now().strftime(
                "%d %b %Y %H:%M"
            )
        )

        try:
            os.remove(name)
        except Exception:
            pass

    except Exception as e:
        print("backup error:", e)


# =========================================================
# AUTO BACKUP LOOP
# =========================================================
async def backup_loop():
    while True:
        try:
            now = datetime.now()

            if (
                now.hour == config.AUTO_BACKUP_HOUR
                and now.minute == 0
            ):
                await create_backup()
                await asyncio.sleep(60)

        except Exception as e:
            print("backup loop error:", e)

        await asyncio.sleep(20)


# =========================================================
# OPTIONAL RESTART LOOP
# =========================================================
async def restart_loop():
    while True:
        try:
            now = datetime.now()

            # contoh:
            # if now.hour == 6 and now.minute == 0:
            #     os._exit(0)

        except Exception as e:
            print("restart loop error:", e)

        await asyncio.sleep(20)
