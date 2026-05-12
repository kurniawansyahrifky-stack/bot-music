# Copyright (c) 2025 AnonymousX1025

# Licensed under the MIT License.

# This file is part of AnonXMusic

from random import randint
from time import time

from pymongo import AsyncMongoClient

from anony import config, logger, userbot


class MongoDB:
    def __init__(self):
        self.mongo = AsyncMongoClient(
            config.MONGO_URL,
            serverSelectionTimeoutMS=12500
        )

        self.db = self.mongo.Anon

        self.admin_list = {}
        self.active_calls = {}
        self.admin_play = []
        self.blacklisted = []
        self.gban_users = []
        self.cmd_delete = []
        self.loop = {}
        self.notified = []

        self.cache = self.db.cache
        self.logger = False

        self.assistant = {}
        self.assistantdb = self.db.assistant

        self.auth = {}
        self.authdb = self.db.auth

        self.chats = []
        self.chatsdb = self.db.chats

        self.lang = {}
        self.langdb = self.db.lang

        self.users = []
        self.usersdb = self.db.users

        self.channel_map = {}
        self.channeldb = self.db.channelmap

        self.ankes = []
        self.ankesdb = self.db.ankes

        self.antispam = self.db.antispam
        self.blacklist = self.db.blacklist
        self.whitelist = self.db.whitelist

        # ================= ANTIBC =================
        self.antibcdb = self.db.antibc
        self.antibc_cache = {}

    async def connect(self) -> None:
        try:
            start = time()

            await self.mongo.admin.command("ping")

            logger.info(
                f"Database connection successful. ({time() - start:.2f}s)"
            )

            await self.load_cache()

        except Exception as e:
            raise SystemExit(
                f"Database connection failed: {type(e).__name__}"
            ) from e

    async def close(self) -> None:
        await self.mongo.close()
        logger.info("Database connection closed.")

    # ================= CACHE =================

    async def get_call(self, chat_id: int) -> bool:
        return chat_id in self.active_calls

    async def add_call(self, chat_id: int) -> None:
        self.active_calls[chat_id] = 1

    async def remove_call(self, chat_id: int) -> None:
        self.active_calls.pop(chat_id, None)

    async def playing(
        self,
        chat_id: int,
        paused: bool = None
    ) -> bool | None:

        if paused is not None:
            self.active_calls[chat_id] = int(not paused)

        return bool(self.active_calls.get(chat_id, 0))

    async def get_admins(
        self,
        chat_id: int,
        reload: bool = False
    ) -> list[int]:

        from anony.helpers._admins import reload_admins

        if chat_id not in self.admin_list or reload:
            self.admin_list[chat_id] = await reload_admins(chat_id)

        return self.admin_list[chat_id]

    async def get_loop(self, chat_id: int) -> int:
        return self.loop.get(chat_id, 0)

    async def set_loop(
        self,
        chat_id: int,
        count: int
    ) -> None:

        self.loop[chat_id] = count

    # ================= ANTISPAM =================

    async def set_antispam(
        self,
        chat_id: int,
        status: bool
    ):

        await self.antispam.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "status": status
                }
            },
            upsert=True
        )

    async def get_antispam(
        self,
        chat_id: int
    ) -> bool:

        data = await self.antispam.find_one(
            {"chat_id": chat_id}
        )

        if not data:
            return False

        return data.get("status", False)

    # ================= ANTIBC =================

    async def set_antibc(
        self,
        chat_id: int,
        status: bool
    ):

        self.antibc_cache[chat_id] = status

        await self.antibcdb.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "status": status
                }
            },
            upsert=True
        )

    async def get_antibc(
        self,
        chat_id: int
    ) -> bool:

        if chat_id in self.antibc_cache:
            return self.antibc_cache[chat_id]

        data = await self.antibcdb.find_one(
            {"chat_id": chat_id}
        )

        if not data:
            self.antibc_cache[chat_id] = False
            return False

        status = data.get("status", False)

        self.antibc_cache[chat_id] = status

        return status

    # ================= BLACKLIST WORD =================

    async def set_blacklist(
        self,
        chat_id: int,
        words: list
    ):

        await self.blacklist.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "words": words
                }
            },
            upsert=True
        )

    async def get_blacklist(
        self,
        chat_id: int
    ) -> list:

        data = await self.blacklist.find_one(
            {"chat_id": chat_id}
        )

        if not data:
            return []

        return data.get("words", [])

    # ================= WHITELIST =================

    async def set_whitelist(
        self,
        chat_id: int,
        users: list
    ):

        await self.whitelist.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "users": users
                }
            },
            upsert=True
        )

    async def get_whitelist(
        self,
        chat_id: int
    ) -> list:

        data = await self.whitelist.find_one(
            {"chat_id": chat_id}
        )

        if not data:
            return []

        return data.get("users", [])

    # ================= AUTH =================

    async def _get_auth(self, chat_id: int) -> set[int]:
        if chat_id not in self.auth:
            doc = await self.authdb.find_one({"_id": chat_id}) or {}

            self.auth[chat_id] = set(doc.get("user_ids", []))

        return self.auth[chat_id]

    async def is_auth(
        self,
        chat_id: int,
        user_id: int
    ) -> bool:

        return user_id in await self._get_auth(chat_id)

    async def add_auth(
        self,
        chat_id: int,
        user_id: int
    ) -> None:

        users = await self._get_auth(chat_id)

        if user_id not in users:
            users.add(user_id)

            await self.authdb.update_one(
                {"_id": chat_id},
                {"$addToSet": {"user_ids": user_id}},
                upsert=True
            )

    async def rm_auth(
        self,
        chat_id: int,
        user_id: int
    ) -> None:

        users = await self._get_auth(chat_id)

        if user_id in users:
            users.discard(user_id)

            await self.authdb.update_one(
                {"_id": chat_id},
                {"$pull": {"user_ids": user_id}}
            )

    # ================= ASSISTANT =================

    async def set_assistant(self, chat_id: int) -> int:
        num = randint(1, len(userbot.clients))

        await self.assistantdb.update_one(
            {"_id": chat_id},
            {"$set": {"num": num}},
            upsert=True,
        )

        self.assistant[chat_id] = num

        return num

    async def get_assistant(self, chat_id: int):
        from anony import anon

        if chat_id not in self.assistant:
            doc = await self.assistantdb.find_one({"_id": chat_id})

            num = doc["num"] if doc else None

            if not num or num > len(anon.clients):
                num = await self.set_assistant(chat_id)

            self.assistant[chat_id] = num

        return anon.clients[self.assistant[chat_id] - 1]

    async def get_client(self, chat_id: int):
        if chat_id not in self.assistant:
            await self.get_assistant(chat_id)

        num = self.assistant[chat_id]

        if num > len(userbot.clients):
            num = await self.set_assistant(chat_id)
            self.assistant[chat_id] = num

        return {
            1: userbot.one,
            2: userbot.two,
            3: userbot.three
        }.get(num)

    # ================= BLACKLIST CHAT =================

    async def add_blacklist(self, chat_id: int) -> None:
        if chat_id not in self.blacklisted:
            self.blacklisted.append(chat_id)

        await self.cache.update_one(
            {"_id": "bl_chats"},
            {"$addToSet": {"chat_ids": chat_id}},
            upsert=True,
        )

    async def del_blacklist(self, chat_id: int) -> None:
        if chat_id in self.blacklisted:
            self.blacklisted.remove(chat_id)

        await self.cache.update_one(
            {"_id": "bl_chats"},
            {"$pull": {"chat_ids": chat_id}},
        )

    async def get_blacklisted(
        self,
        chat: bool = False
    ) -> list[int]:

        if not self.blacklisted:
            doc = await self.cache.find_one({"_id": "bl_chats"})

            self.blacklisted.extend(
                doc.get("chat_ids", []) if doc else []
            )

        return self.blacklisted

    # ================= GBAN USER =================

    async def add_gban(self, user_id: int) -> None:
        if user_id not in self.gban_users:
            self.gban_users.append(user_id)

        await self.cache.update_one(
            {"_id": "gban_users"},
            {"$addToSet": {"user_ids": user_id}},
            upsert=True,
        )

    async def del_gban(self, user_id: int) -> None:
        if user_id in self.gban_users:
            self.gban_users.remove(user_id)

        await self.cache.update_one(
            {"_id": "gban_users"},
            {"$pull": {"user_ids": user_id}},
        )

    async def get_gban(self) -> list[int]:
        if not self.gban_users:
            doc = await self.cache.find_one({"_id": "gban_users"})

            self.gban_users.extend(
                doc.get("user_ids", []) if doc else []
            )

        return self.gban_users

    # ================= CMD DELETE =================

    async def get_cmd_delete(self, chat_id: int) -> bool:
        if chat_id not in self.cmd_delete:
            doc = await self.chatsdb.find_one({"_id": chat_id})

            if doc and doc.get("cmd_delete"):
                self.cmd_delete.append(chat_id)

        return chat_id in self.cmd_delete

    async def set_cmd_delete(
        self,
        chat_id: int,
        delete: bool = False
    ) -> None:

        if delete:
            if chat_id not in self.cmd_delete:
                self.cmd_delete.append(chat_id)
        else:
            if chat_id in self.cmd_delete:
                self.cmd_delete.remove(chat_id)

        await self.chatsdb.update_one(
            {"_id": chat_id},
            {"$set": {"cmd_delete": delete}},
            upsert=True,
        )

    # ================= LANGUAGE =================

    async def set_lang(
        self,
        chat_id: int,
        lang_code: str
    ):

        await self.langdb.update_one(
            {"_id": chat_id},
            {"$set": {"lang": lang_code}},
            upsert=True,
        )

        self.lang[chat_id] = lang_code

    async def get_lang(self, chat_id: int) -> str:
        if chat_id not in self.lang:
            doc = await self.langdb.find_one({"_id": chat_id})

            self.lang[chat_id] = (
                doc["lang"] if doc else config.LANG_CODE
            )

        return self.lang[chat_id]

    # ================= ANKES =================

    async def add_ankes(
        self,
        chat_id: int,
        expired: int
    ) -> None:

        if chat_id not in self.ankes:
            self.ankes.append(chat_id)

        await self.ankesdb.update_one(
            {"_id": chat_id},
            {
                "$set": {
                    "expired": expired
                }
            },
            upsert=True
        )

    async def remove_ankes(self, chat_id: int) -> None:
        if chat_id in self.ankes:
            self.ankes.remove(chat_id)

        await self.ankesdb.delete_one(
            {"_id": chat_id}
        )

    async def get_ankes(self) -> list:
        if not self.ankes:
            self.ankes.extend(
                [chat["_id"] async for chat in self.ankesdb.find()]
            )

        return self.ankes

    async def is_ankes(self, chat_id: int) -> bool:
        return chat_id in await self.get_ankes()

    async def get_expired(self, chat_id: int):
        data = await self.ankesdb.find_one(
            {"_id": chat_id}
        )

        if not data:
            return None

        return data.get("expired")

    async def set_expired(
        self,
        chat_id: int,
        expired: int
    ):

        await self.ankesdb.update_one(
            {"_id": chat_id},
            {
                "$set": {
                    "expired": expired
                }
            },
            upsert=True
        )

    # ================= LOGGER =================

    async def is_logger(self) -> bool:
        return self.logger

    async def get_logger(self) -> bool:
        doc = await self.cache.find_one({"_id": "logger"})

        if doc:
            self.logger = doc["status"]

        return self.logger

    async def set_logger(self, status: bool) -> None:
        self.logger = status

        await self.cache.update_one(
            {"_id": "logger"},
            {"$set": {"status": status}},
            upsert=True,
        )

    # ================= PLAY MODE =================

    async def get_play_mode(self, chat_id: int) -> bool:
        if chat_id not in self.admin_play:
            doc = await self.chatsdb.find_one({"_id": chat_id})

            if doc and doc.get("admin_play"):
                self.admin_play.append(chat_id)

        return chat_id in self.admin_play

    async def set_play_mode(
        self,
        chat_id: int,
        remove: bool = False
    ) -> None:

        if remove:
            if chat_id in self.admin_play:
                self.admin_play.remove(chat_id)
        else:
            if chat_id not in self.admin_play:
                self.admin_play.append(chat_id)

        await self.chatsdb.update_one(
            {"_id": chat_id},
            {"$set": {"admin_play": not remove}},
            upsert=True,
        )

    # ================= SUDO =================

    async def add_sudo(self, user_id: int) -> None:
        await self.cache.update_one(
            {"_id": "sudoers"},
            {"$addToSet": {"user_ids": user_id}},
            upsert=True
        )

    async def del_sudo(self, user_id: int) -> None:
        await self.cache.update_one(
            {"_id": "sudoers"},
            {"$pull": {"user_ids": user_id}}
        )

    async def get_sudoers(self) -> list[int]:
        doc = await self.cache.find_one({"_id": "sudoers"})

        return doc.get("user_ids", []) if doc else []

    # ================= USERS =================

    async def is_user(self, user_id: int) -> bool:
        return user_id in self.users

    async def add_user(self, user_id: int) -> None:
        if user_id not in self.users:
            self.users.append(user_id)

            await self.usersdb.update_one(
                {"_id": user_id},
                {"$set": {"_id": user_id}},
                upsert=True
            )

    async def rm_user(self, user_id: int) -> None:
        if user_id in self.users:
            self.users.remove(user_id)

        await self.usersdb.delete_one({"_id": user_id})

    async def get_users(self) -> list:
        if not self.users:
            self.users.extend(
                [user["_id"] async for user in self.usersdb.find()]
            )

        return self.users

    # ================= CHAT LIST =================

    async def is_chat(self, chat_id: int) -> bool:
        return chat_id in self.chats

    async def add_chat(self, chat_id: int) -> None:
        if chat_id not in self.chats:
            self.chats.append(chat_id)

            await self.chatsdb.update_one(
                {"_id": chat_id},
                {"$set": {"_id": chat_id}},
                upsert=True
            )

    async def rm_chat(self, chat_id: int) -> None:
        if chat_id in self.chats:
            self.chats.remove(chat_id)

        await self.chatsdb.delete_one({"_id": chat_id})

    async def get_chats(self) -> list:
        if not self.chats:
            self.chats.extend(
                [chat["_id"] async for chat in self.chatsdb.find()]
            )

        return self.chats

    # ================= CHANNEL MAP =================

    async def set_channel_map(
        self,
        group_id: int,
        channel_id: int
    ) -> None:

        self.channel_map[group_id] = channel_id

        await self.channeldb.update_one(
            {"_id": group_id},
            {"$set": {"channel_id": channel_id}},
            upsert=True,
        )

    async def get_channel_map(self, group_id: int):
        if group_id not in self.channel_map:
            doc = await self.channeldb.find_one({"_id": group_id})

            if doc:
                self.channel_map[group_id] = doc["channel_id"]

        return self.channel_map.get(group_id)

    async def del_channel_map(self, group_id: int) -> None:
        self.channel_map.pop(group_id, None)

        await self.channeldb.delete_one({"_id": group_id})

    # ================= CACHE LOAD =================

    async def load_cache(self) -> None:
        await self.get_chats()
        await self.get_users()
        await self.get_blacklisted(True)
        await self.get_gban()
        await self.get_logger()

        logger.info("Database cache loaded.")


# ================= PLAY CHANNEL LINK DB =================

class PlayChannelDB:
    def __init__(self):
        self.mongo = AsyncMongoClient(
            config.MONGO_URL,
            serverSelectionTimeoutMS=12500
        )

        self.db = self.mongo.Anon
        self.col = self.db.playchannels

        self.links = {}

    async def connect(self):
        try:
            await self.mongo.admin.command("ping")

            logger.info("PlayChannelDB connected.")

            await self.load_cache()

        except Exception as e:
            raise SystemExit(
                f"PlayChannelDB failed: {type(e).__name__}"
            )

    async def load_cache(self):
        async for doc in self.col.find():
            self.links[doc["_id"]] = doc["channel_id"]

    async def set_link(
        self,
        group_id: int,
        channel_id: int
    ):

        self.links[group_id] = channel_id

        await self.col.update_one(
            {"_id": group_id},
            {"$set": {"channel_id": channel_id}},
            upsert=True
        )

    async def get_link(self, group_id: int):
        return self.links.get(group_id)

    async def del_link(self, group_id: int):
        self.links.pop(group_id, None)

        await self.col.delete_one(
            {"_id": group_id}
        )


db = MongoDB()
