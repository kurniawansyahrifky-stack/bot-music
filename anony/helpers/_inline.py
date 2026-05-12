from pyrogram import types
from anony import app, config, lang
from anony.core.lang import lang_codes


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=f"✕ {text} ✕",
                        callback_data="cancel_dl"
                    )
                ]
            ]
        )

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:

        keyboard = []

        if status:
            keyboard.append(
                [
                    self.ikb(
                        text=f"༒︎ {status} ༒︎",
                        callback_data=f"controls status {chat_id}"
                    )
                ]
            )

        elif timer:
            keyboard.append(
                [
                    self.ikb(
                        text=f"༒︎ {timer} ༒︎",
                        callback_data=f"controls status {chat_id}"
                    )
                ]
            )

        if not remove:
            keyboard.append(
                [
                    self.ikb(
                        text="◁",
                        callback_data=f"controls resume {chat_id}"
                    ),
                    self.ikb(
                        text="Ⅱ",
                        callback_data=f"controls pause {chat_id}"
                    ),
                    self.ikb(
                        text="↺",
                        callback_data=f"controls replay {chat_id}"
                    ),
                    self.ikb(
                        text="▷▷",
                        callback_data=f"controls skip {chat_id}"
                    ),
                    self.ikb(
                        text="✕",
                        callback_data=f"controls stop {chat_id}"
                    ),
                ]
            )

        return self.ikm(keyboard)

    def help_markup(
        self,
        _lang: dict,
        back: bool = False,
        page: int = 1
    ) -> types.InlineKeyboardMarkup:

        if back:

            rows = [
                [
                    self.ikb(
                        text="⬅ ʙᴀᴄᴋ",
                        callback_data="help home"
                    ),
                    self.ikb(
                        text="✘ ᴄʟᴏsᴇ",
                        callback_data="help close"
                    ),
                ]
            ]

        else:

            # PAGE 1
            if page == 1:

                cbs = [
                    "admins",
                    "auth",
                    "blist",
                    "lang",
                    "ping",
                    "play",
                    "queue",
                    "stats",
                    "sudo"
                ]

                names = [
                    "⌬ ᴀᴅᴍɪɴs ⌬",
                    "⌬ ᴀᴜᴛʜ ⌬",
                    "⌬ ʙʟɪsᴛ ⌬",
                    "⌬ ʟᴀɴɢ ⌬",
                    "⌬ ᴘɪɴɢ ⌬",
                    "⌬ ᴘʟᴀʏ ⌬",
                    "⌬ ǫᴜᴇᴜᴇ ⌬",
                    "⌬ sᴛᴀᴛs ⌬",
                    "⌬ sᴜᴅᴏ ⌬"
                ]

                buttons = [
                    self.ikb(
                        text=names[i],
                        callback_data=f"help {cb}"
                    )
                    for i, cb in enumerate(cbs)
                ]

                rows = [
                    buttons[i:i + 3]
                    for i in range(0, len(buttons), 3)
                ]

                rows.append(
                    [
                        self.ikb(
                            text="➡ ɴᴇxᴛ",
                            callback_data="help page2"
                        ),
                        self.ikb(
                            text="✘ ᴄʟᴏsᴇ",
                            callback_data="help close"
                        )
                    ]
                )

            # PAGE 2
            else:

                cbs = [
                    "tagall",
                    "translate",
                    "groupinfo",
                    "ai",
                    "tourl",
                    "pinterest",
                    "lyrics",
                    "gcast",
                    "speedtest"
                ]

                names = [
                    "⌬ ᴛᴀɢᴀʟʟ ⌬",
                    "⌬ ᴛʀᴀɴsʟᴀᴛᴇ ⌬",
                    "⌬ ɢʀᴏᴜᴘɪɴғᴏ ⌬",
                    "⌬ ᴀɪ ɢᴘᴛ ⌬",
                    "⌬ ᴛᴏ ᴜʀʟ ⌬",
                    "⌬ ᴘɪɴᴛᴇʀᴇsᴛ ⌬",
                    "⌬ ʟʏʀɪᴄs ⌬",
                    "⌬ ɢᴄᴀsᴛ ⌬",
                    "⌬ sᴘᴇᴇᴅᴛᴇsᴛ ⌬"
                ]

                buttons = [
                    self.ikb(
                        text=names[i],
                        callback_data=f"help {cb}"
                    )
                    for i, cb in enumerate(cbs)
                ]

                rows = [
                    buttons[i:i + 3]
                    for i in range(0, len(buttons), 3)
                ]

                rows.append(
                    [
                        self.ikb(
                            text="⬅ ʙᴀᴄᴋ",
                            callback_data="help back"
                        ),
                        self.ikb(
                            text="✘ ᴄʟᴏsᴇ",
                            callback_data="help close"
                        )
                    ]
                )

        return self.ikm(rows)

    def lang_markup(
        self,
        _lang: str
    ) -> types.InlineKeyboardMarkup:

        langs = lang.get_languages()

        buttons = [
            self.ikb(
                text=(
                    f"⌬ {name} ({code}) "
                    f"{'✔️' if code == _lang else ''}"
                ),
                callback_data=f"lang_change {code}",
            )
            for code, name in langs.items()
        ]

        rows = [
            buttons[i:i + 2]
            for i in range(0, len(buttons), 2)
        ]

        return self.ikm(rows)

    def ping_markup(
        self,
        text: str
    ) -> types.InlineKeyboardMarkup:

        return self.ikm(
            [
                [
                    self.ikb(
                        text="༒︎ sᴜᴘᴘᴏʀᴛ ᴄᴇɴᴛᴇʀ ༒︎",
                        url=config.SUPPORT_CHAT
                    )
                ]
            ]
        )

    def play_queued(
        self,
        chat_id: int,
        item_id: str,
        _text: str
    ) -> types.InlineKeyboardMarkup:

        return self.ikm(
            [
                [
                    self.ikb(
                        text=f"♬ {_text} ♬",
                        callback_data=(
                            f"controls force "
                            f"{chat_id} {item_id}"
                        )
                    )
                ]
            ]
        )

    def queue_markup(
        self,
        chat_id: int,
        _text: str,
        playing: bool
    ) -> types.InlineKeyboardMarkup:

        _action = (
            "pause"
            if playing
            else "resume"
        )

        return self.ikm(
            [
                [
                    self.ikb(
                        text=f"♬ {_text} ♬",
                        callback_data=(
                            f"controls {_action} "
                            f"{chat_id} q"
                        )
                    )
                ]
            ]
        )

    def settings_markup(
        self,
        lang: dict,
        admin_only: bool,
        cmd_delete: bool,
        language: str,
        chat_id: int
    ) -> types.InlineKeyboardMarkup:

        return self.ikm(
            [
                [
                    self.ikb(
                        text="⌬ ᴘʟᴀʏ ᴍᴏᴅᴇ ⌬",
                        callback_data="settings"
                    ),
                    self.ikb(
                        text=f"〔 {admin_only} 〕",
                        callback_data="settings play"
                    ),
                ],
                [
                    self.ikb(
                        text="⌬ ᴄᴍᴅ ᴅᴇʟᴇᴛᴇ ⌬",
                        callback_data="settings"
                    ),
                    self.ikb(
                        text=f"〔 {cmd_delete} 〕",
                        callback_data="settings delete"
                    ),
                ],
                [
                    self.ikb(
                        text="⌬ ʟᴀɴɢᴜᴀɢᴇ ⌬",
                        callback_data="settings"
                    ),
                    self.ikb(
                        text=f"〔 {lang_codes[language]} 〕",
                        callback_data="language"
                    ),
                ],
            ]
        )

    def start_key(
        self,
        lang: dict,
        private: bool = False
    ) -> types.InlineKeyboardMarkup:

        rows = [
            [
                self.ikb(
                    text="༒︎ ᴀᴅᴅ ᴍᴇ ᴛᴏ ɢʀᴏᴜᴘ ༒︎",
                    url=f"https://t.me/{app.username}?startgroup=true",
                )
            ],
            [
                self.ikb(
                    text="♬ ʜᴇʟᴘ ᴍᴇɴᴜ ♬",
                    callback_data="help"
                )
            ],
            [
                self.ikb(
                    text="⌬ sᴜᴘᴘᴏʀᴛ ⌬",
                    url=config.SUPPORT_CHAT
                ),
                self.ikb(
                    text="⌬ ᴄʜᴀɴɴᴇʟ ⌬",
                    url=config.SUPPORT_CHANNEL
                ),
            ],
        ]

        if private:

            rows += [
                [
                    self.ikb(
                        text="༒︎ ᴅᴇᴠᴇʟᴏᴘᴇʀ ༒︎",
                        url="https://t.me/Brsik23",
                    )
                ]
            ]

        else:

            rows += [
                [
                    self.ikb(
                        text="⌬ ʟᴀɴɢᴜᴀɢᴇ ⌬",
                        callback_data="language"
                    )
                ]
            ]

        return self.ikm(rows)

    def yt_key(
        self,
        link: str
    ) -> types.InlineKeyboardMarkup:

        return self.ikm(
            [
                [
                    self.ikb(
                        text="❐ ᴄᴏᴘʏ",
                        copy_text=link
                    ),
                    self.ikb(
                        text="▶ ʏᴏᴜᴛᴜʙᴇ",
                        url=link
                    ),
                ]
            ]
        )
