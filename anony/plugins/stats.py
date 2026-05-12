# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import platform
import sys

import psutil
from pyrogram import __version__, filters, types
from pytgcalls import __version__ as pytgver

from anony import app, config, db, lang, userbot
from anony.plugins import all_modules


# BISA DI PRIVATE DAN GROUP
@app.on_message(filters.command(["stats"]) & ~app.bl_users)
@lang.language()
async def _stats(_, m: types.Message):
    sent = await m.reply_photo(
        photo=config.PING_IMG,
        caption="Fetching bot statistics...",
    )

    pid = os.getpid()

    # ===== DATABASE COUNT =====
    total_groups = len(await db.get_chats())
    total_users = len(await db.get_users())
    total_blacklist = len(await db.get_blacklisted())
    total_gban = len(await db.get_gban())
    total_sudo = len(app.sudoers)

    # ===== BOT INFO =====
    _utext = (
        f"**❖ {app.name} BOT STATISTICS ❖**\n\n"
        f"**➥ Assistant Clients :** `{len(userbot.clients)}`\n"
        f"**➥ Auto Leave Time :** `{config.AUTO_LEAVE}`\n"
        f"**➥ Blacklisted Chats :** `{total_blacklist}`\n"
        f"**➥ Gbanned Users :** `{total_gban}`\n"
        f"**➥ Sudo Users :** `{total_sudo}`\n"
        f"**➥ Served Chats :** `{total_groups}`\n"
        f"**➥ Served Users :** `{total_users}`\n"
    )

    # ===== OWNER / SUDO SYSTEM INFO =====
    if m.from_user.id in app.sudoers:
        process = psutil.Process(pid)
        storage = psutil.disk_usage("/")

        _utext += (
            f"\n**❖ SYSTEM STATISTICS ❖**\n\n"
            f"**➥ Modules Loaded :** `{len(all_modules)}`\n"
            f"**➥ OS :** `{platform.system()}`\n"
            f"**➥ RAM Usage :** `{process.memory_info().rss / 1024**2:.2f} MB`\n"
            f"**➥ Total RAM :** `{round(psutil.virtual_memory().total / (1024.0**3))} GB`\n"
            f"**➥ CPU Usage :** `{process.cpu_percent(interval=1.0)}%`\n"
            f"**➥ CPU Cores :** `{psutil.cpu_count()}`\n"
            f"**➥ Disk Used :** `{storage.used / (1024.0**3):.2f} GB`\n"
            f"**➥ Disk Total :** `{storage.total / (1024.0**3):.2f} GB`\n"
            f"**➥ Python :** `{sys.version.split()[0]}`\n"
            f"**➥ Pyrogram :** `{__version__}`\n"
            f"**➥ PyTgCalls :** `{pytgver}`\n"
        )

    await sent.edit_caption(_utext)
