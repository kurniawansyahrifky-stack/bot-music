from datetime import datetime, timedelta

from pyrogram import filters
from pytz import timezone

from anony import app, db, config


# ================= ADD ANKES =================

@app.on_message(
    filters.command("addankes") &
    filters.user(config.OWNER_ID)
)
async def addankes(_, message):

    if len(message.command) < 3:
        return await message.reply_text(
            "Gunakan:\n/addankes -100xxxx 30"
        )

    chat_id = int(message.command[1])
    days = int(message.command[2])

    expire = datetime.now(
        timezone("Asia/Jakarta")
    ) + timedelta(days=days)

    expire_unix = int(expire.timestamp())

    await db.add_ankes(
        chat_id,
        expire_unix
    )

    return await message.reply_text(
        f"Berhasil menambahkan ankes:\n\n"
        f"Chat ID: `{chat_id}`\n"
        f"Expired: `{days}` hari"
    )


# ================= DELETE ANKES =================

@app.on_message(
    filters.command("delankes") &
    filters.user(config.OWNER_ID)
)
async def delankes(_, message):

    if len(message.command) < 2:
        return await message.reply_text(
            "Gunakan:\n/delankes -100xxxx"
        )

    chat_id = int(message.command[1])

    await db.remove_ankes(chat_id)

    return await message.reply_text(
        f"Berhasil menghapus ankes:\n`{chat_id}`"
    )


# ================= CEK ANKES =================

@app.on_message(
    filters.command("cekankes") &
    filters.user(config.OWNER_ID)
)
async def cekankes(_, message):

    if len(message.command) < 2:
        return await message.reply_text(
            "Gunakan:\n/cekankes -100xxxx"
        )

    chat_id = int(message.command[1])

    status = await db.is_ankes(chat_id)

    if not status:
        return await message.reply_text(
            "Group tidak terdaftar."
        )

    expired = await db.get_expired(chat_id)

    if expired:
        expired_text = datetime.fromtimestamp(
            expired,
            tz=timezone("Asia/Jakarta")
        ).strftime("%d-%m-%Y %H:%M")
    else:
        expired_text = "Tidak ada"

    return await message.reply_text(
        f"STATUS ANKES\n\n"
        f"Chat ID: `{chat_id}`\n"
        f"Expired: `{expired_text}`"
    )
