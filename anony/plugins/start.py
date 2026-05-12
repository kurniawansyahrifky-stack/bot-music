from pyrogram import filters, types
from pyrogram.errors import UserNotParticipant

from anony import app, config, db, lang
from anony.helpers import buttons

FORCE_CHANNEL = "@storegarf"


@app.on_message(filters.command("start") & ~app.bl_users)
@lang.language()
async def start(_, message: types.Message):

    args = message.text.split(maxsplit=1)

    # =====================================
    # FORCE SUB CHECK
    # =====================================

    try:

        member = await app.get_chat_member(
            FORCE_CHANNEL,
            message.from_user.id
        )

        if member.status in [
            "left",
            "kicked"
        ]:
            raise UserNotParticipant

    except Exception:

        keyboard = types.InlineKeyboardMarkup(
            [
                [
                    types.InlineKeyboardButton(
                        text="📢 JOIN CHANNEL",
                        url=f"https://t.me/{FORCE_CHANNEL.replace('@', '')}"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        text="🔄 REFRESH",
                        callback_data="start_refresh"
                    )
                ]
            ]
        )

        return await message.reply_photo(
            photo=config.START_IMG,
            caption="❌ Kamu harus join channel terlebih dahulu!",
            reply_markup=keyboard
        )

    # =====================================
    # DATABASE
    # =====================================

    total_users = len(await db.get_users())
    total_groups = len(await db.get_chats())

    # =====================================
    # HELP MENU
    # =====================================

    if len(args) > 1:

        if args[1] == "help":

            return await message.reply_photo(
                photo=config.START_IMG,
                caption=message.lang["help_menu"],
                reply_markup=buttons.help_markup(
                    message.lang,
                    page=1
                )
            )

    # =====================================
    # START TEXT
    # =====================================

    text = (
        f"✧ ━━『 <b>HEY {message.from_user.first_name}</b> 』━━ ✧\n\n"

        f"<b>I AM {app.name}</b>\n"
        "AN ADVANCED VOICE CHAT MUSIC ASSISTANT\n"
        "WITH POWERFUL FEATURES AND SMOOTH STREAMING.\n\n"

        "<blockquote>"
        "◈ TAP THE HELP MENU BELOW TO EXPLORE MY COMMANDS ◈"
        "</blockquote>\n\n"

        "<blockquote>"
        f"◈ TOTAL USERS : <code>{total_users}</code>\n"
        f"◈ TOTAL GROUPS : <code>{total_groups}</code>"
        "</blockquote>"
    )

    # =====================================
    # SEND START MESSAGE
    # =====================================

    await message.reply_photo(
        photo=config.START_IMG,
        caption=text,
        reply_markup=buttons.start_key(
            message.lang,
            private=True
        )
    )
