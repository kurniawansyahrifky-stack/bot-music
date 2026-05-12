import re

from pyrogram import errors, filters, types
from pyrogram.errors import UserNotParticipant

from anony import anon, app, db, lang, queue, tg, yt, config
from anony.helpers import admin_check, buttons, can_manage_vc


@app.on_callback_query(filters.regex("cancel_dl") & ~app.bl_users)
@lang.language()
async def cancel_dl(_, query: types.CallbackQuery):
    await query.answer()
    await tg.cancel(query)


@app.on_callback_query(filters.regex("controls") & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _controls(_, query: types.CallbackQuery):
    args = query.data.split()
    action, chat_id = args[1], int(args[2])
    qaction = len(args) == 4
    user = query.from_user.mention

    if not await db.get_call(chat_id):
        try:
            return await query.answer(query.lang["not_playing"], show_alert=True)
        except errors.QueryIdInvalid:
            try:
                await query.message.delete()
            except Exception:
                pass
            return

    if action == "status":
        return await query.answer()

    await query.answer(query.lang["processing"], show_alert=True)

    if action == "pause":
        if not await db.playing(chat_id):
            return await query.answer(query.lang["play_already_paused"], show_alert=True)

        await anon.pause(chat_id)

        if qaction:
            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(
                    chat_id,
                    query.lang["paused"],
                    False
                )
            )

        status = query.lang["paused"]
        reply = query.lang["play_paused"].format(user)

    elif action == "resume":
        if await db.playing(chat_id):
            return await query.answer(query.lang["play_not_paused"], show_alert=True)

        await anon.resume(chat_id)

        if qaction:
            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(
                    chat_id,
                    query.lang["playing"],
                    True
                )
            )

        status = query.lang["playing"]
        reply = query.lang["play_resumed"].format(user)

    elif action == "skip":
        await anon.play_next(chat_id)

        status = query.lang["skipped"]
        reply = query.lang["play_skipped"].format(user)

    elif action == "force":

        pos, media = queue.check_item(
            chat_id,
            args[3]
        )

        if not media or pos == -1:
            return await query.edit_message_text(
                query.lang["play_expired"]
            )

        m_id = queue.get_current(chat_id).message_id

        queue.force_add(
            chat_id,
            media,
            remove=pos
        )

        try:
            await app.delete_messages(
                chat_id=chat_id,
                message_ids=[m_id, media.message_id],
                revoke=True
            )

            media.message_id = None

        except Exception:
            pass

        msg = await app.send_message(
            chat_id=chat_id,
            text=query.lang["play_next"]
        )

        if not media.file_path:
            media.file_path = await yt.download(
                media.id,
                video=media.video
            )

        media.message_id = msg.id

        return await anon.play_media(
            chat_id,
            msg,
            media
        )

    elif action == "replay":

        media = queue.get_current(chat_id)

        media.user = user

        await anon.replay(chat_id)

        status = query.lang["replayed"]
        reply = query.lang["play_replayed"].format(user)

    elif action == "stop":

        await anon.stop(chat_id)

        status = query.lang["stopped"]
        reply = query.lang["play_stopped"].format(user)

    try:

        if action in [
            "skip",
            "replay",
            "stop"
        ]:

            await query.message.reply_text(
                reply,
                quote=False
            )

            await query.message.delete()

        else:

            mtext = re.sub(
                r"\n\n<blockquote>.*?</blockquote>",
                "",
                query.message.caption.html
                or query.message.text.html,
                flags=re.DOTALL,
            )

            keyboard = buttons.controls(
                chat_id,
                status=status
            )

            await query.edit_message_text(
                f"{mtext}\n\n<blockquote>{reply}</blockquote>",
                reply_markup=keyboard
            )

    except Exception:
        pass


# ==========================================
# HELP MENU CALLBACK
# ==========================================

@app.on_callback_query(filters.regex("^help") & ~app.bl_users)
@lang.language()
async def _help(_, query: types.CallbackQuery):

    data = query.data.split()

    if len(data) == 1:

        return await query.answer(
            url=f"https://t.me/{app.username}?start=help"
        )

    cmd = data[1]

    if cmd == "close":

        try:

            await query.message.delete()

            if query.message.reply_to_message:
                await query.message.reply_to_message.delete()

        except Exception:
            pass

        return

    elif cmd == "home":

        return await query.edit_message_media(
            media=types.InputMediaPhoto(
                media=config.START_IMG,
                caption=query.lang["help_menu"]
            ),
            reply_markup=buttons.help_markup(
                query.lang,
                page=1
            )
        )

    elif cmd == "page2":

        return await query.edit_message_media(
            media=types.InputMediaPhoto(
                media=config.START_IMG,
                caption=query.lang["help_menu"]
            ),
            reply_markup=buttons.help_markup(
                query.lang,
                page=2
            )
        )

    elif cmd == "back":

        return await query.edit_message_media(
            media=types.InputMediaPhoto(
                media=config.START_IMG,
                caption=query.lang["help_menu"]
            ),
            reply_markup=buttons.help_markup(
                query.lang,
                page=1
            )
        )

    return await query.edit_message_media(
        media=types.InputMediaPhoto(
            media=config.START_IMG,
            caption=query.lang.get(
                f"help_{cmd}",
                query.lang["help_menu"]
            )
        ),
        reply_markup=buttons.help_markup(
            query.lang,
            back=True
        )
    )


# ==========================================
# SETTINGS CALLBACK
# ==========================================

@app.on_callback_query(filters.regex("settings") & ~app.bl_users)
@lang.language()
@admin_check
async def _settings_cb(_, query: types.CallbackQuery):

    cmd = query.data.split()

    if len(cmd) == 1:
        return await query.answer()

    await query.answer(
        query.lang["processing"],
        show_alert=True
    )

    chat_id = query.message.chat.id

    _admin = await db.get_play_mode(chat_id)
    _delete = await db.get_cmd_delete(chat_id)
    _language = await db.get_lang(chat_id)

    if cmd[1] == "delete":

        _delete = not _delete

        await db.set_cmd_delete(
            chat_id,
            _delete
        )

    elif cmd[1] == "play":

        await db.set_play_mode(
            chat_id,
            _admin
        )

        _admin = not _admin

    await query.edit_message_reply_markup(
        reply_markup=buttons.settings_markup(
            query.lang,
            _admin,
            _delete,
            _language,
            chat_id,
        )
    )


# ==========================================
# FORCE SUB / START REFRESH
# ==========================================

FORCE_CHANNEL = "@storegarf"


@app.on_callback_query(filters.regex("start_refresh") & ~app.bl_users)
@lang.language()
async def start_refresh(_, query: types.CallbackQuery):

    try:

        member = await app.get_chat_member(
            FORCE_CHANNEL,
            query.from_user.id
        )

        if member.status in [
            "left",
            "kicked"
        ]:
            raise UserNotParticipant

    except Exception:

        return await query.answer(
            "❌ Kamu belum join channel terlebih dahulu!",
            show_alert=True
        )

    total_users = len(await db.get_users())
    total_groups = len(await db.get_chats())

    text = (
        "✨ <b>WELCOME TO MY PREMIUM HELP PANEL</b> ✨\n\n"

        f"☃️ <b>Name :</b> {query.from_user.mention}\n"
        f"🤖 <b>Bot :</b> {app.name}\n"
        f"👥 <b>Total Users :</b> <code>{total_users}</code>\n"
        f"🏘 <b>Total Groups :</b> <code>{total_groups}</code>\n\n"

        "⌬ <i>Advanced Music System With Modern Features</i>\n"
        "⌬ <i>Fast Streaming • AI • Pinterest • ToURL</i>\n"
        "⌬ <i>Premium Inline Interface & VC Support</i>"
    )

    await query.message.edit_media(
        media=types.InputMediaPhoto(
            media=config.START_IMG,
            caption=text
        ),
        reply_markup=buttons.start_key(
            query.lang,
            True
        )
    )
