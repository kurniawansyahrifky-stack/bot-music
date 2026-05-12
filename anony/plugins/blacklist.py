from pyrogram import filters, types
from anony import app, db, lang


@app.on_message(filters.command(["blacklist", "unblacklist", "whitelist"]) & app.sudoers)
@lang.language()
async def _blacklist(_, m: types.Message):
    if len(m.command) < 2:
        return await m.reply_text(m.lang["bl_usage"].format(m.command[0]))

    try:
        chat_id = m.command[1]
        if not str(chat_id).startswith("@"):
            chat_id = int(chat_id)
        else:
            chat_id = (await app.get_chat(chat_id)).id
    except Exception:
        return await m.reply_text(m.lang["bl_invalid"])

    if m.command[0] == "blacklist":
        if chat_id in db.blacklisted or chat_id in app.bl_users:
            return await m.reply_text(m.lang["bl_already"])

        # blacklist group
        if str(chat_id).startswith("-100"):
            await db.add_blacklist(chat_id)
            await m.reply_text("✅ Group berhasil diblacklist. Bot akan keluar dari group.")
            try:
                await app.leave_chat(chat_id)
            except Exception:
                pass

        # global blacklist user
        else:
            app.bl_users.add(chat_id)
            await db.add_blacklist(chat_id)
            await m.reply_text("✅ User berhasil di global blacklist.")

    else:
        if chat_id not in db.blacklisted and chat_id not in app.bl_users:
            return await m.reply_text(m.lang["bl_not"])

        # whitelist group
        if str(chat_id).startswith("-100"):
            await db.del_blacklist(chat_id)
            await m.reply_text("✅ Group berhasil dihapus dari blacklist.")

        # un-gban user
        else:
            app.bl_users.discard(chat_id)
            await db.del_blacklist(chat_id)
            await m.reply_text("✅ User berhasil dihapus dari global blacklist.")
