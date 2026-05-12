# anony/plugins/wherebot.py

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatType

from anony import app, userbot, config, db

OWNER_ID = getattr(config, "OWNER_ID", 0)


# =========================================================
# HELPERS
# =========================================================
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def make_link(chat):
    if getattr(chat, "username", None):
        return f"https://t.me/{chat.username}"
    return None


def get_main_assistant():
    """
    Project kamu hanya memakai assistant utama userbot.one
    """
    return getattr(userbot, "one", None)


# =========================================================
# /WHEREBOT
# =========================================================
@app.on_message(filters.command("wherebot") & filters.private)
async def wherebot_handler(_, message: Message):
    if not message.from_user or not is_owner(message.from_user.id):
        return

    client = get_main_assistant()

    if not client:
        return await message.reply_text(
            "❌ Assistant tidak aktif."
        )

    text = "🤖 <b>Assistant berada di grup:</b>\n\n"
    found = False
    seen = set()

    try:
        async for dialog in client.get_dialogs():
            try:
                chat = dialog.chat

                if chat.type not in (
                    ChatType.GROUP,
                    ChatType.SUPERGROUP,
                ):
                    continue

                if chat.id in seen:
                    continue

                seen.add(chat.id)

                title = chat.title or "Unknown Group"
                link = make_link(chat)

                text += f"• <b>{title}</b>\n"
                text += f"  <code>{chat.id}</code>\n"

                if link:
                    text += f"  {link}\n"

                text += "\n"
                found = True

                if len(text) > 3500:
                    await message.reply_text(
                        text,
                        disable_web_page_preview=True,
                    )
                    text = ""

            except Exception:
                continue

        if not found:
            return await message.reply_text(
                "❌ Assistant tidak berada di grup mana pun."
            )

        if text.strip():
            await message.reply_text(
                text,
                disable_web_page_preview=True,
            )

    except Exception as e:
        await message.reply_text(
            f"❌ Error:\n<code>{e}</code>"
        )


# =========================================================
# /WHEREPLAY
# =========================================================
@app.on_message(filters.command("whereplay") & filters.private)
async def whereplay_handler(_, message: Message):
    if not message.from_user or not is_owner(message.from_user.id):
        return

    try:
        active_calls = getattr(db, "active_calls", {})

        if not active_calls:
            return await message.reply_text(
                "🎵 Tidak ada grup yang sedang memutar musik."
            )

        text = "🎵 <b>Grup yang sedang memutar musik:</b>\n\n"
        found = False

        for chat_id in list(active_calls.keys()):
            try:
                chat = await app.get_chat(chat_id)

                title = chat.title or "Unknown Group"
                link = make_link(chat)

                text += f"• <b>{title}</b>\n"
                text += f"  <code>{chat.id}</code>\n"

                if link:
                    text += f"  {link}\n"

                text += "\n"
                found = True

            except Exception:
                continue

        if not found:
            return await message.reply_text(
                "🎵 Tidak ada grup yang sedang memutar musik."
            )

        await message.reply_text(
            text,
            disable_web_page_preview=True,
        )

    except Exception as e:
        await message.reply_text(
            f"❌ Error:\n<code>{e}</code>"
        )
