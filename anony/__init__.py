# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import time
import asyncio
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
__version__ = "3.0.3"

from config import Config
config = Config()
config.check()

tasks = []
boot = time.time()

# =========================
# MAIN BOT TOKEN CLIENT
# =========================
from anony.core.bot import Bot
app = Bot()

# =========================
# ENSURE DIRECTORIES
# =========================
from anony.core.dir import ensure_dirs
ensure_dirs()

# =========================
# USERBOT SESSION ENGINE
# =========================
from anony.core.userbot import Userbot
userbot = Userbot()

# =========================
# DATABASE
# =========================
from anony.core.mongo import MongoDB, PlayChannelDB
db = MongoDB()
playdb = PlayChannelDB()

# =========================
# LANGUAGE SYSTEM
# =========================
from anony.core.lang import Language
lang = Language()

# =========================
# TELEGRAM / YOUTUBE ENGINE
# =========================
from anony.core.telegram import Telegram
from anony.core.youtube import YouTube

tg = Telegram()
yt = YouTube()

# =========================
# HELPERS
# =========================
from anony.helpers import Queue, Thumbnail
queue = Queue()
thumb = Thumbnail()

# =========================
# VC CALL ENGINE
# =========================
from anony.core.calls import TgCall
anon = TgCall()


# =========================
# STARTUP LOGGER
# =========================
async def startup_log():
    try:
        me = await app.get_me()
        logger.info(f"Main Bot Started As @{me.username}")
    except Exception as e:
        logger.error(f"Main Bot Start Failed: {e}")

    try:
        ub = await userbot.get_me()
        logger.info(f"Userbot Session Loaded As @{ub.username}")
    except Exception as e:
        logger.error(f"Userbot Session Failed: {e}")


# =========================
# SAFE STOP
# =========================
async def stop() -> None:
    logger.info("Stopping Garfield Music Core...")

    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.exceptions.CancelledError:
            pass

    await app.exit()
    await userbot.exit()
    await db.close()
    await thumb.close()

    logger.info("Stopped Successfully.\n")
