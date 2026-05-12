# anony/plugins/restartbot.py
# Owner-only restart command with:
# - Animated progress bar
# - Restart via systemctl
# - Automatic success notification after bot is back online
# - Error logging to LOG_GROUP_ID
#
# Command:
# /restartbot

import asyncio
import os
import traceback

from pyrogram import filters
from pyrogram.types import Message

from anony import app, db, config

OWNER_ID = getattr(config, "OWNER_ID", 0)
LOG_GROUP_ID = getattr(config, "LOG_GROUP_ID", None)
SERVICE_NAME = getattr(config, "SERVICE_NAME", "garfilmusic")


# =========================================================
# HELPERS
# =========================================================

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def send_log(title: str, content: str):
    """Kirim log ke LOG_GROUP_ID."""
    if not LOG_GROUP_ID:
        print(f"[RESTARTBOT] {title}\n{content}")
        return

    try:
        await app.send_message(
            LOG_GROUP_ID,
            f"<b>🛠 {title}</b>\n\n<pre>{content[:3800]}</pre>",
        )
    except Exception as e:
        print(f"[RESTARTBOT LOG ERROR] {e}")


def progress_bar(percent: int) -> str:
    filled = percent // 10
    empty = 10 - filled
    return "█" * filled + "░" * empty


# =========================================================
# RESTART COMMAND
# =========================================================

@app.on_message(filters.command("restartbot") & filters.private)
async def restartbot_handler(_, message: Message):
    if not message.from_user:
        return

    if not is_owner(message.from_user.id):
        return

    try:
        msg = await message.reply_text(
            "♻️ <b>Preparing restart...</b>\n\n"
            f"<code>{progress_bar(0)}</code> 0%"
        )

        steps = [
            (10, "🔍 Checking system..."),
            (25, "📦 Saving session..."),
            (45, "🧠 Flushing cache..."),
            (65, "🔄 Restarting service..."),
        ]

        for percent, text in steps:
            await asyncio.sleep(0.8)
            await msg.edit_text(
                f"{text}\n\n"
                f"<code>{progress_bar(percent)}</code> {percent}%"
            )

        # Simpan message info agar setelah bot online bisa diedit
        await db.cache.update_one(
            {"_id": "restart_message"},
            {
                "$set": {
                    "chat_id": msg.chat.id,
                    "message_id": msg.id,
                }
            },
            upsert=True,
        )

        await send_log(
            "RESTARTBOT START",
            f"Requested by: {message.from_user.id}\n"
            f"Service: {SERVICE_NAME}",
        )

        # Delay kecil biar progress terlihat
        await asyncio.sleep(1)

        # Restart service
        os.system(f"systemctl restart {SERVICE_NAME}")

    except Exception as e:
        error_text = f"{e}\n\n{traceback.format_exc()}"

        await send_log("RESTARTBOT ERROR", error_text)

        try:
            await message.reply_text(
                "❌ <b>Restart gagal</b>\n\n"
                f"<code>{e}</code>"
            )
        except Exception:
            pass


# =========================================================
# AUTO NOTIFY AFTER BOT ONLINE AGAIN
# =========================================================

async def notify_restart_success():
    try:
        # Tunggu bot stabil
        await asyncio.sleep(5)

        data = await db.cache.find_one({"_id": "restart_message"})
        if not data:
            return

        chat_id = data.get("chat_id")
        message_id = data.get("message_id")

        if not chat_id or not message_id:
            return

        # Update 85%
        try:
            await app.edit_message_text(
                chat_id,
                message_id,
                "⏳ <b>Waiting for startup...</b>\n\n"
                f"<code>{progress_bar(85)}</code> 85%",
            )
            await asyncio.sleep(1.5)
        except Exception:
            pass

        # Final success message
        success_text = (
            "🎉 <b>Restart Completed Successfully!</b>\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🤖 <b>Garfil Music Bot</b>\n"
            "🟢 Status : <b>Online</b>\n"
            f"⚡ Service : <code>{SERVICE_NAME}</code>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Bot siap digunakan kembali."
        )

        try:
            await app.edit_message_text(
                chat_id,
                message_id,
                success_text,
            )
        except Exception:
            await app.send_message(chat_id, success_text)

        await send_log(
            "RESTARTBOT SUCCESS",
            f"Service {SERVICE_NAME} restarted successfully.",
        )

        # Hapus cache restart
        await db.cache.delete_one({"_id": "restart_message"})

    except Exception as e:
        await send_log(
            "RESTART SUCCESS NOTIFY ERROR",
            f"{e}\n\n{traceback.format_exc()}",
        )


# Jalankan auto notifier saat plugin dimuat
try:
    asyncio.create_task(notify_restart_success())
except Exception:
    pass
