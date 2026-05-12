from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def tagall_time_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("2 Menit", callback_data="tagall_2"),
                InlineKeyboardButton("5 Menit", callback_data="tagall_5"),
            ],
            [
                InlineKeyboardButton("10 Menit", callback_data="tagall_10"),
                InlineKeyboardButton("30 Menit", callback_data="tagall_30"),
            ],
            [
                InlineKeyboardButton("60 Menit", callback_data="tagall_60"),
                InlineKeyboardButton("∞ Unlimited", callback_data="tagall_0"),
            ],
            [
                InlineKeyboardButton("🛒 My Store", url="https://t.me/officialhyperion"),
            ],
            [
                InlineKeyboardButton("❌ Batal", callback_data="tagall_cancel"),
                InlineKeyboardButton("🗑 Clear", callback_data="tagall_clear"),
            ],
        ]
    )


def tagall_stop_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❌ Stop Tagall", callback_data="tagall_stop"),
            ]
        ]
    )
