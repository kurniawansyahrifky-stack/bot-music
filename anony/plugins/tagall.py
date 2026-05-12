import asyncio
import contextlib
import random
import time

from pyrogram import filters, types, enums, errors
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus

from anony import app, lang

tagall_tasks = {}
tagall_messages = {}
tagall_payload = {}
tagall_mentioned = {}
tagall_stop_events = {}

FORCE_SUB_CHANNEL = "storegarf"
STORE_URL = "https://t.me/storegarf"

MAX_UNLIMITED = 10000
AUTO_CLEAR_TIME = 180

BLACKLIST_USERNAMES = [
    "garfileds",
    "Brsik23"
]


def duration_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "1 Menit",
                callback_data="tagall_1"
            ),
            InlineKeyboardButton(
                "5 Menit",
                callback_data="tagall_5"
            )
        ],
        [
            InlineKeyboardButton(
                "10 Menit",
                callback_data="tagall_10"
            ),
            InlineKeyboardButton(
                "30 Menit",
                callback_data="tagall_30"
            )
        ],
        [
            InlineKeyboardButton(
                "60 Menit",
                callback_data="tagall_60"
            ),
            InlineKeyboardButton(
                "∞ Unlimited",
                callback_data="tagall_0"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Batal",
                callback_data="tagall_cancel"
            )
        ]
    ])


def clear_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🗑 Clear Semua",
                callback_data="tagall_clear"
            )
        ]
    ])


def store_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🛍️ My Store",
                url=STORE_URL
            )
        ]
    ])


def force_sub_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 Join Channel",
                url=STORE_URL
            )
        ]
    ])


async def clear_all_tagall(chat_id):

    msgs = tagall_messages.get(chat_id, [])

    if not msgs:
        return

    for i in range(0, len(msgs), 100):

        chunk = msgs[i:i + 100]

        with contextlib.suppress(Exception):

            await app.delete_messages(
                chat_id,
                chunk
            )

    tagall_messages.pop(chat_id, None)


async def delayed_clear(chat_id):

    await asyncio.sleep(AUTO_CLEAR_TIME)

    await clear_all_tagall(chat_id)


async def is_admin_or_owner(message):

    if message.from_user.id in app.sudoers:
        return True

    try:

        member = await app.get_chat_member(
            message.chat.id,
            message.from_user.id
        )

        return member.status in [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ]

    except Exception:
        return False


async def check_force_sub(user_id):

    if user_id in app.sudoers:
        return True

    try:

        member = await app.get_chat_member(
            FORCE_SUB_CHANNEL,
            user_id
        )

        return member.status not in [
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED
        ]

    except Exception:
        return False


def make_mention(user):

    name = user.first_name.replace(
        "[",
        ""
    ).replace(
        "]",
        ""
    )

    return f"[{name}](tg://user?id={user.id})"


def is_blacklisted(user):

    if user.username:

        return user.username.lower() in [
            x.lower()
            for x in BLACKLIST_USERNAMES
        ]

    return False


@app.on_message(
    filters.command(
        ["tagall", "all", "mentionall"]
    )
    & filters.group
    & ~app.bl_users
)
@lang.language()
async def tagall_start(_, m: types.Message):

    chat_id = m.chat.id

    if not await is_admin_or_owner(m):

        return await m.reply_text(
            "❌ Lo bukan admin grub nyet."
        )

    if not await check_force_sub(
        m.from_user.id
    ):

        return await m.reply_text(
            "⚠️ Join channel support dulu.",
            reply_markup=force_sub_markup()
        )

    if chat_id in tagall_tasks:

        return await m.reply_text(
            "⚠️ Tagall sedang berjalan."
        )

    text = (
        m.text.split(None, 1)[1]
        if len(m.text.split(None, 1)) > 1
        else "📢 Attention Everyone!"
    )

    # PREVIEW OTOMATIS TANPA NAMPILIN LINK
    chat_username = m.chat.username

    if chat_username:
        preview_link = f"https://t.me/{chat_username}"
    else:
        preview_link = STORE_URL

    tagall_payload[chat_id] = {
        "text": text,
        "preview": preview_link
    }

    panel = await m.reply_text(
        "✨ Pilih durasi:",
        reply_markup=duration_markup()
    )

    tagall_messages.setdefault(
        chat_id,
        []
    ).append(panel.id)


@app.on_message(
    filters.command(
        ["cancel", "stop"]
    )
    & filters.group
)
async def stop_tagall_cmd(_, m: types.Message):

    chat_id = m.chat.id

    if not await is_admin_or_owner(m):

        return await m.reply_text(
            "❌ Lo bukan admin grub nyet."
        )

    event = tagall_stop_events.get(chat_id)

    if event:
        event.set()

    task = tagall_tasks.get(chat_id)

    if task:
        task.cancel()

    tagall_tasks.pop(chat_id, None)

    msg = await m.reply_text(
        "🛑 Tagall berhasil dihentikan paksa.",
        reply_markup=clear_markup()
    )

    tagall_messages.setdefault(
        chat_id,
        []
    ).append(msg.id)

    asyncio.create_task(
        delayed_clear(chat_id)
    )


async def run_tagall(query, minutes):

    chat_id = query.message.chat.id

    old_task = tagall_tasks.get(chat_id)

    if old_task:
        old_task.cancel()

    data = tagall_payload.get(chat_id)

    if not data:
        return

    promo = data["text"]
    preview_link = data["preview"]

    stop_time = (
        time.time() + (minutes * 60)
        if minutes else None
    )

    stop_event = asyncio.Event()

    tagall_stop_events[chat_id] = stop_event

    tagall_mentioned[chat_id] = set()

    with contextlib.suppress(Exception):
        await query.message.delete()

    async def runner():

        sent_count = 0
        block = []

        try:

            async for member in app.get_chat_members(chat_id):

                if stop_event.is_set():
                    return

                current_task = tagall_tasks.get(chat_id)

                if current_task != asyncio.current_task():
                    return

                if stop_time and time.time() >= stop_time:
                    break

                if (
                    not stop_time
                    and sent_count >= MAX_UNLIMITED
                ):
                    break

                user = member.user

                if user.is_bot:
                    continue

                if user.is_deleted:
                    continue

                if is_blacklisted(user):
                    continue

                if user.id in tagall_mentioned[chat_id]:
                    continue

                tagall_mentioned[chat_id].add(
                    user.id
                )

                block.append(
                    make_mention(user)
                )

                sent_count += 1

                # 3 USER PER PESAN
                if len(block) < 3:
                    continue

                mention_text = " ".join(block)

                # HIDDEN LINK BUAT PREVIEW
                body = (
                    f"[ㅤ]({preview_link})\n"
                    f"{promo}\n\n"
                    f"{mention_text}"
                )

                try:

                    msg = await app.send_message(
                        chat_id,
                        body,
                        parse_mode=enums.ParseMode.MARKDOWN,
                        disable_web_page_preview=False,
                        reply_markup=store_markup()
                    )

                    tagall_messages.setdefault(
                        chat_id,
                        []
                    ).append(msg.id)

                    block.clear()

                    # SMOOTH CEPAT ANTI FLOOD
                    await asyncio.sleep(
                        random.uniform(1.2, 1.8)
                    )

                except errors.FloodWait as fw:

                    await asyncio.sleep(
                        fw.value + 2
                    )

                except Exception:
                    continue

            # SISA USER
            if block and not stop_event.is_set():

                mention_text = " ".join(block)

                body = (
                    f"[ㅤ]({preview_link})\n"
                    f"{promo}\n\n"
                    f"{mention_text}"
                )

                with contextlib.suppress(Exception):

                    msg = await app.send_message(
                        chat_id,
                        body,
                        parse_mode=enums.ParseMode.MARKDOWN,
                        disable_web_page_preview=False,
                        reply_markup=store_markup()
                    )

                    tagall_messages.setdefault(
                        chat_id,
                        []
                    ).append(msg.id)

            if not stop_event.is_set():

                done = await app.send_message(
                    chat_id,
                    (
                        f"✅ Tagall selesai.\n"
                        f"👥 Total Mentioned: {sent_count}\n"
                        f"⚡ Smooth Anti Flood Active\n"
                        f"🗑 Auto clear 3 menit."
                    ),
                    reply_markup=clear_markup()
                )

                tagall_messages.setdefault(
                    chat_id,
                    []
                ).append(done.id)

                asyncio.create_task(
                    delayed_clear(chat_id)
                )

        except asyncio.CancelledError:
            return

        finally:

            current_task = tagall_tasks.get(chat_id)

            if current_task == asyncio.current_task():

                tagall_tasks.pop(chat_id, None)
                tagall_payload.pop(chat_id, None)
                tagall_mentioned.pop(chat_id, None)
                tagall_stop_events.pop(chat_id, None)

    task = asyncio.create_task(
        runner()
    )

    tagall_tasks[chat_id] = task


@app.on_callback_query(
    filters.regex(
        r"^tagall_(\d+|cancel|clear)$"
    )
)
async def tagall_callbacks(
    _,
    query: types.CallbackQuery
):

    chat_id = query.message.chat.id

    data = query.data.split("_")[1]

    await query.answer()

    if data == "cancel":

        event = tagall_stop_events.get(chat_id)

        if event:
            event.set()

        task = tagall_tasks.get(chat_id)

        if task:
            task.cancel()

        tagall_tasks.pop(chat_id, None)

        with contextlib.suppress(Exception):

            await query.message.edit_text(
                "🛑 Tagall berhasil dihentikan paksa.",
                reply_markup=clear_markup()
            )

        asyncio.create_task(
            delayed_clear(chat_id)
        )

        return

    if data == "clear":

        event = tagall_stop_events.get(chat_id)

        if event:
            event.set()

        task = tagall_tasks.get(chat_id)

        if task:
            task.cancel()

        tagall_tasks.pop(chat_id, None)

        await clear_all_tagall(chat_id)

        with contextlib.suppress(Exception):
            await query.message.delete()

        return

    await run_tagall(
        query,
        int(data)
    )
