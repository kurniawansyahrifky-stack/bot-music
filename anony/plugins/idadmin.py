# Copyright (c) 2025 AnonymousX1025

from pyrogram import filters, enums
from pyrogram.types import Message

from anony import app

# ================================
# COMMAND /id
# ================================

@app.on_message(filters.command("id"))
async def get_id(_, message: Message):

    # /id biasa = id group
    if len(message.command) == 1 and not message.reply_to_message:
        if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            await message.reply_text(
                f"""
╭─「 GROUP INFO 」
├ Nama : {message.chat.title}
├ ID Grup : `{message.chat.id}`
╰──────────────
"""
            )
        else:
            await message.reply_text(
                f"""
╭─「 USER INFO 」
├ Nama : {message.from_user.first_name}
├ Username : @{message.from_user.username if message.from_user.username else 'Tidak Ada'}
├ ID User : `{message.from_user.id}`
╰──────────────
"""
            )
        return

    # /id reply user
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        await message.reply_text(
            f"""
╭─「 USER INFO 」
├ Nama : {user.first_name}
├ Username : @{user.username if user.username else 'Tidak Ada'}
├ ID User : `{user.id}`
╰──────────────
"""
        )
        return

    # /id @username
    if len(message.command) > 1:
        username = message.command[1]
        try:
            if username.startswith("@"):
                user = await app.get_users(username)
            else:
                user = await app.get_users(f"@{username}")

            await message.reply_text(
                f"""
╭─「 USERNAME INFO 」
├ Nama : {user.first_name}
├ Username : @{user.username if user.username else 'Tidak Ada'}
├ ID User : `{user.id}`
╰──────────────
"""
            )
        except Exception as e:
            await message.reply_text(f"❌ User tidak ditemukan\n`{e}`")


# ================================
# COMMAND /cekadmin
# ================================

@app.on_message(filters.command("cekadmin") & filters.group)
async def cek_admin(_, message: Message):

    teks = f"╭─「 ADMIN GROUP : {message.chat.title} 」\n"

    no = 1
    async for member in app.get_chat_members(
        message.chat.id,
        filter=enums.ChatMembersFilter.ADMINISTRATORS
    ):
        user = member.user

        jabatan = "Owner" if member.status == enums.ChatMemberStatus.OWNER else "Admin"

        teks += (
            f"\n{no}. {user.first_name}"
            f"\n   ├ Username : @{user.username if user.username else 'Tidak Ada'}"
            f"\n   ├ ID : `{user.id}`"
            f"\n   ╰ Jabatan : {jabatan}\n"
        )
        no += 1

    teks += "\n╰──────────────"
    await message.reply_text(teks)
