from pyrogram import filters, types
from anony import app, db, lang


@app.on_message(filters.command(["gban", "ungban"]) & app.sudoers)
@lang.language()
async def _gban(_, m: types.Message):
    if len(m.command) < 2 and not m.reply_to_message:
        return await m.reply_text(
            "Usage:\n/gban user_id or reply user\n/ungban user_id or reply user"
        )

    try:
        if m.reply_to_message:
            user_id = m.reply_to_message.from_user.id
        else:
            user_id = int(m.command[1])
    except Exception:
        return await m.reply_text("Invalid user id.")

    if user_id == app.owner:
        return await m.reply_text("Owner cannot be gban.")

    if user_id in await db.get_sudoers():
        return await m.reply_text("Sudo users cannot be gban.")

    if m.command[0] == "gban":
        if user_id in app.bl_users:
            return await m.reply_text("User already globally banned.")

        app.bl_users.add(user_id)
        await db.add_gban(user_id)
        return await m.reply_text(f"Successfully gbanned `{user_id}`")

    else:
        if user_id not in app.bl_users:
            return await m.reply_text("User not gbanned.")

        app.bl_users.discard(user_id)
        await db.del_gban(user_id)
        return await m.reply_text(f"Successfully ungbanned `{user_id}`")
