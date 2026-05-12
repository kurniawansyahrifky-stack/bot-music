import random

from pyrogram import filters
from pyrogram.types import Message

from anony import app
from anony.helpers.mafia_roles import get_available_roles
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

FORCE_SUB_CHANNEL = "@storegarf"
FORCE_SUB_URL = "https://t.me/storegarf"
# Menyimpan game aktif per chat
MAFIA_GAMES = {}


async def check_force_sub(message: Message) -> bool:
    try:
        member = await app.get_chat_member(
            FORCE_SUB_CHANNEL,
            message.from_user.id
        )

        if member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ):
            return True

    except Exception:
        pass

    await message.reply_text(
        "❌ Kamu harus join channel terlebih dahulu untuk menggunakan game Mafia.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📢 Join Channel",
                        url=FORCE_SUB_URL
                    )
                ]
            ]
        )
    )
    return False

@app.on_message(filters.command("mafia") & filters.group)
async def create_mafia(_, message: Message):
    # Cek apakah user sudah join channel wajib
    if not await check_force_sub(message):
        return

    chat_id = message.chat.id

    if chat_id in MAFIA_GAMES:
        return await message.reply_text(
            "❌ Game Mafia sudah dibuat di grup ini."
        )

    MAFIA_GAMES[chat_id] = {
        "players": [],
        "started": False,
        "roles": {}
    }

    await message.reply_text(
        "🕵️ Game Mafia berhasil dibuat!\n\n"
        "👥 Ketik /join untuk bergabung."
    )


@app.on_message(filters.command("join") & filters.group)
async def join_mafia(_, message: Message):
    # Cek apakah user sudah join channel wajib
    if not await check_force_sub(message):
        return

    chat_id = message.chat.id
    user = message.from_user

    if chat_id not in MAFIA_GAMES:
        return await message.reply_text(
            "❌ Belum ada game. Gunakan /mafia terlebih dahulu."
        )

    game = MAFIA_GAMES[chat_id]

    if game["started"]:
        return await message.reply_text(
            "❌ Game sudah dimulai."
        )

    if user.id in game["players"]:
        return await message.reply_text(
            "❌ Kamu sudah bergabung."
        )

    game["players"].append(user.id)

    await message.reply_text(
        f"✅ {user.mention} bergabung!\n"
        f"👥 Total pemain: {len(game['players'])}"
    )


@app.on_message(filters.command("startgame") & filters.group)
async def start_mafia(_, message: Message):
    # Cek apakah user sudah join channel wajib
    if not await check_force_sub(message):
        return

    chat_id = message.chat.id

    if chat_id not in MAFIA_GAMES:
        return await message.reply_text(
            "❌ Tidak ada game aktif."
        )

    game = MAFIA_GAMES[chat_id]

    if game["started"]:
        return await message.reply_text(
            "❌ Game sudah dimulai."
        )

    players = game["players"]

    if len(players) < 4:
        return await message.reply_text(
            "❌ Minimal 4 pemain."
        )

    roles = get_available_roles()
    random.shuffle(roles)

    selected_roles = roles[:len(players)]

    for user_id, role in zip(players, selected_roles):
        game["roles"][user_id] = role

        try:
            await app.send_message(
                user_id,
                f"🕵️ Role kamu: **{role}**"
            )
        except Exception:
            pass

    game["started"] = True

    await message.reply_text(
        "🎮 Game Mafia dimulai!\n"
        "📩 Role telah dikirim ke private chat masing-masing."
    )


@app.on_message(filters.command("status") & filters.group)
async def mafia_status(_, message: Message):
    chat_id = message.chat.id

    if chat_id not in MAFIA_GAMES:
        return await message.reply_text(
            "❌ Tidak ada game aktif."
        )

    game = MAFIA_GAMES[chat_id]

    await message.reply_text(
        "📊 Status Game Mafia\n\n"
        f"👥 Players: {len(game['players'])}\n"
        f"🎮 Started: {game['started']}"
    )


@app.on_message(filters.command("endgame") & filters.group)
async def end_mafia(_, message: Message):
    chat_id = message.chat.id

    if chat_id not in MAFIA_GAMES:
        return await message.reply_text(
            "❌ Tidak ada game aktif."
        )

    del MAFIA_GAMES[chat_id]

    await message.reply_text(
        "🛑 Game Mafia diakhiri."
    )
