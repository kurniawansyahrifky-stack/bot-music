# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
import signal
import importlib
import os
import sys
import gc
import zipfile
import glob
import traceback
import time

from datetime import datetime
from contextlib import suppress

from anony import (
    anon,
    app,
    config,
    db,
    playdb,
    logger,
    stop,
    thumb,
    userbot,
    yt
)

from anony.plugins import all_modules


LOG_GROUP = -1003949678131


# ==============================
# AUTO BACKUP DAILY
# ==============================

async def auto_backup():

    while True:

        try:

            now = datetime.now()

            if (
                now.hour == config.AUTO_BACKUP_HOUR
                and now.minute == 0
            ):

                zip_name = (
                    f"{app.username}_"
                    f"{now.strftime('%Y-%m-%d_%H%M')}.zip"
                )

                with zipfile.ZipFile(
                    zip_name,
                    "w",
                    zipfile.ZIP_DEFLATED
                ) as zf:

                    for folder, _, files in os.walk("."):

                        if (
                            "venv" in folder
                            or "__pycache__" in folder
                            or ".git" in folder
                        ):
                            continue

                        for file in files:

                            file_path = os.path.join(
                                folder,
                                file
                            )

                            zf.write(file_path)

                await app.send_document(
                    LOG_GROUP,
                    zip_name,
                    caption=(
                        "✅ Auto backup "
                        "berhasil dikirim."
                    )
                )

                os.remove(zip_name)

                logger.info(
                    "Auto backup sent successfully."
                )

                await asyncio.sleep(60)

        except Exception as e:

            logger.error(
                f"Auto Backup Error: {e}"
            )

            with suppress(Exception):

                await app.send_message(
                    LOG_GROUP,
                    f"⚠️ Auto Backup Error\n\n"
                    f"<code>{e}</code>"
                )

        await asyncio.sleep(30)


# ==============================
# AUTO RESTART DAILY
# ==============================

async def auto_restart():

    while True:

        try:

            now = datetime.now()

            if (
                now.hour
                == config.AUTO_RESTART_HOUR
                and now.minute == 0
            ):

                logger.info(
                    "Daily auto restart triggered."
                )

                # ==========================
                # NOTIF SEBELUM RESTART
                # ==========================

                with suppress(Exception):

                    await app.send_message(
                        LOG_GROUP,
                        "⚠️ <b>Automatic Restart Scheduled</b>\n\n"
                        "⏳ Bot akan restart otomatis "
                        "15 detik lagi.\n"
                        "🎵 Semua voice chat sementara "
                        "akan terputus.\n"
                        "🔄 Sistem akan kembali online "
                        "secara otomatis."
                    )

                # ==========================
                # TUNGGU 15 DETIK
                # ==========================

                await asyncio.sleep(15)

                # ==========================
                # NOTIF RESTART
                # ==========================

                with suppress(Exception):

                    await app.send_message(
                        LOG_GROUP,
                        "♻️ <b>Restarting Bot System...</b>\n\n"
                        "🧹 Membersihkan cache dan memory...\n"
                        "🚀 Memulai ulang seluruh sistem bot..."
                    )

                logger.info(
                    "Restarting full bot system."
                )

                # ==========================
                # STOP SEMUA VC AKTIF
                # ==========================

                with suppress(Exception):

                    if hasattr(app, "active_chats"):

                        for chat_id in list(app.active_chats):

                            with suppress(Exception):

                                await anon.stop_stream(chat_id)

                # ==========================
                # BERSIHKAN MEMORY
                # ==========================

                gc.collect()

                # ==========================
                # RESTART PROCESS
                # ==========================

                os.execv(
                    sys.executable,
                    [sys.executable] + sys.argv
                )

        except Exception as e:

            logger.error(
                f"Auto Restart Error: {e}"
            )

            with suppress(Exception):

                await app.send_message(
                    LOG_GROUP,
                    f"⚠️ Auto Restart Error\n\n"
                    f"<code>{e}</code>"
                )

        await asyncio.sleep(20)


# ==============================
# SMART CACHE CLEANER
# ==============================

async def auto_cache_clean():

    while True:

        try:

            cleaned = 0

            now = time.time()

            folders = [
                "downloads",
                "cache",
                "temp",
                "tmp",
                ".cache",
                "downloads/spotify",
                "downloads/youtube"
            ]

            for folder in folders:

                if not os.path.isdir(folder):
                    continue

                for f in glob.glob(
                    f"{folder}/**",
                    recursive=True
                ):

                    with suppress(Exception):

                        if not os.path.isfile(f):
                            continue

                        file_age = (
                            now
                            - os.path.getmtime(f)
                        )

                        if file_age > 1200:

                            os.remove(f)

                            cleaned += 1

            gc.collect()

            logger.info(
                f"Smart cleaner removed "
                f"{cleaned} files."
            )

            with suppress(Exception):

                await app.send_message(
                    LOG_GROUP,
                    f"🧹 Cache cleaner "
                    f"removed {cleaned} files."
                )

        except Exception as e:

            logger.error(
                f"Auto Cache Cleaner Error: {e}"
            )

            with suppress(Exception):

                await app.send_message(
                    LOG_GROUP,
                    f"⚠️ Cache Cleaner Error\n\n"
                    f"<code>{e}</code>"
                )

        await asyncio.sleep(1200)


# ==============================
# STARTUP NOTIFICATION
# ==============================

async def startup_notify():

    try:

        me = await app.get_me()

        txt = (
            "🚀 <b>Bot Running Successfully</b>\n\n"
            f"🤖 <b>Bot:</b> {me.mention}\n"
            f"🆔 <b>ID:</b> <code>{me.id}</code>\n"
            f"📛 <b>Name:</b> "
            f"<b>{me.first_name}</b>\n"
            f"🔗 <b>Username:</b> "
            f"@{me.username}"
        )

        await app.send_message(
            LOG_GROUP,
            txt
        )

    except Exception as e:

        logger.error(
            f"Startup notify failed: {e}"
        )

# ==============================
# GLOBAL ERROR LOGGER
# ==============================

def setup_global_error_handler(loop):

    def handle_exception(loop, context):

        exc = context.get("exception")

        if not exc:
            return

        try:
            asyncio.create_task(
                send_error_to_log(exc)
            )
        except Exception as e:
            logger.error(
                f"Global Error Handler Failed: {e}"
            )

    loop.set_exception_handler(
        handle_exception
    )


async def send_error_to_log(exc):

    try:
        tb = traceback.extract_tb(
            exc.__traceback__
        )

        file_name = "Unknown"
        line_no = "Unknown"

        if tb:
            last = tb[-1]
            file_name = last.filename
            line_no = last.lineno

        error_name = type(exc).__name__
        error_text = str(exc)

        full_trace = "".join(
            traceback.format_exception(
                type(exc),
                exc,
                exc.__traceback__
            )
        )

        text = (
            "⚠️ <b>SYSTEM ERROR DETECTED</b>\n\n"
            f"📅 <b>Date:</b> "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📂 <b>File:</b> "
            f"<code>{file_name}</code>\n"
            f"📍 <b>Line:</b> "
            f"<code>{line_no}</code>\n"
            f"🧾 <b>Error:</b>\n"
            f"<code>{error_name}: {error_text}</code>\n\n"
            f"<pre>{full_trace[:3500]}</pre>"
        )

        logger.error(full_trace)

        await app.send_message(
            LOG_GROUP,
            text
        )

    except Exception as e:
        logger.error(
            f"send_error_to_log failed: {e}"
        )

def wrap_all_handlers():

    def wrap_callback(callback):

        async def wrapped(client, *args, **kwargs):
            try:
                return await callback(client, *args, **kwargs)
            except Exception as e:
                await send_error_to_log(e)
                raise

        return wrapped

    total = 0

    for _, handlers in app.dispatcher.groups.items():
        for handler in handlers:
            if hasattr(handler, "callback"):
                handler.callback = wrap_callback(
                    handler.callback
                )
                total += 1

    logger.info(
        f"Wrapped {total} handlers with error logger."
    )
    
# ==============================
# IDLE
# ==============================

async def idle():

    loop = asyncio.get_running_loop()

    stop_event = asyncio.Event()

    for sig in (
        signal.SIGINT,
        signal.SIGTERM,
        signal.SIGABRT
    ):

        with suppress(NotImplementedError):

            loop.add_signal_handler(
                sig,
                stop_event.set
            )

    await stop_event.wait()


# ==============================
# MAIN
# ==============================

async def main():

    loop = asyncio.get_running_loop()

    setup_global_error_handler(loop)

    await db.connect()

    await playdb.connect()

    await app.boot()

    await userbot.boot()

    await anon.boot()

    await thumb.start()

    for module in all_modules:

        importlib.import_module(
            f"anony.plugins.{module}"
        )
    
    wrap_all_handlers()
    
    logger.info(
        f"Loaded {len(all_modules)} modules."
    )

    if config.COOKIES_URL:

        await yt.save_cookies(
            config.COOKIES_URL
        )

    sudoers = await db.get_sudoers()

    app.sudoers.update(sudoers)

    app.bl_users.update(
        await db.get_blacklisted()
    )

    logger.info(
        f"Loaded {len(app.sudoers)} sudo users."
    )
    
    with suppress(Exception):

        await app.send_message(
            LOG_GROUP,
            "✅ Semua sistem background "
            "berhasil dijalankan."
        )

    asyncio.create_task(
        auto_backup()
    )

    asyncio.create_task(
        auto_restart()
    )

    asyncio.create_task(
        auto_cache_clean()
    )

    asyncio.create_task(
        startup_notify()
    )

    await idle()
    await stop()
    


if __name__ == "__main__":

    try:

        asyncio.get_event_loop().run_until_complete(
            main()
        )

    except KeyboardInterrupt:

        pass
