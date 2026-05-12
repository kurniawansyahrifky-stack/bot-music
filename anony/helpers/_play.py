import asyncio
from pyrogram import enums, errors, types
from anony import app, config, db, playdb, logger, queue, yt
from anony.helpers import utils

FORCE_SUB_CHANNEL = "@storegarf"


async def force_sub_check(m):
    try:
        member = await app.get_chat_member(FORCE_SUB_CHANNEL, m.from_user.id)
        if member.status in [
            enums.ChatMemberStatus.LEFT,
            enums.ChatMemberStatus.BANNED,
        ]:
            raise Exception("not joined")
        return True
    except Exception:
        btn = types.InlineKeyboardMarkup(
            [
                [
                    types.InlineKeyboardButton(
                        "Join Channel",
                        url="https://t.me/storegarf"
                    )
                ]
            ]
        )
        await m.reply_text(
            f"⚠️ Anda wajib join {FORCE_SUB_CHANNEL} terlebih dahulu sebelum menggunakan bot ini.",
            reply_markup=btn
        )
        return False


def checkUB(play):
    async def wrapper(_, m: types.Message):
        if not m.from_user:
            return await m.reply_text(m.lang["play_user_invalid"])

        if not await force_sub_check(m):
            return

        command = m.command[0].lower()
        channel_mode = command.startswith("c")

        group_id = m.chat.id
        target_id = group_id

        if channel_mode:
            linked = await playdb.get_link(group_id)
            if not linked:
                return await m.reply_text("❌ belum ada linked channel. gunakan /playchannel")
            target_id = linked

        if m.chat.type != enums.ChatType.SUPERGROUP:
            await m.reply_text(m.lang["play_chat_invalid"])
            return await app.leave_chat(group_id)

        if not m.reply_to_message and (
            len(m.command) < 2 or (len(m.command) == 2 and m.command[1] == "-f")
        ):
            return await m.reply_text(m.lang["play_usage"])

        if len(queue.get_queue(target_id)) >= config.QUEUE_LIMIT:
            return await m.reply_text(
                m.lang["play_queue_full"].format(config.QUEUE_LIMIT)
            )

        force = command.endswith("force") or (
            len(m.command) > 1 and "-f" in m.command[1]
        )

        video = command.startswith("v") or command.startswith("cv")
        url = utils.get_url(m)

        if url and yt.invalid(url):
            return await m.reply_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

        m3u8 = url and not yt.valid(url)

        play_mode = await db.get_play_mode(group_id)
        if play_mode or force:
            adminlist = await db.get_admins(group_id)
            if (
                m.from_user.id not in adminlist
                and not await db.is_auth(group_id, m.from_user.id)
                and m.from_user.id not in app.sudoers
            ):
                return await m.reply_text(m.lang["play_admin"])

        if target_id not in db.active_calls:
            client = await db.get_client(target_id)

            try:
                member = await app.get_chat_member(target_id, client.id)
                if member.status in [
                    enums.ChatMemberStatus.BANNED,
                    enums.ChatMemberStatus.RESTRICTED,
                ]:
                    try:
                        await app.unban_chat_member(chat_id=target_id, user_id=client.id)
                    except Exception:
                        return await m.reply_text(
                            m.lang["play_banned"].format(
                                app.name,
                                client.id,
                                client.mention,
                                f"@{client.username}" if client.username else None,
                            )
                        )

            except errors.ChatAdminRequired:
                return await m.reply_text("❌ bot token harus admin di target chat/channel.")

            except (errors.UserNotParticipant, errors.exceptions.bad_request_400.UserNotParticipant):
                try:
                    target_chat = await app.get_chat(target_id)

                    if target_chat.username:
                        invite_link = target_chat.username
                    else:
                        invite_link = target_chat.invite_link
                        if not invite_link:
                            invite_link = await app.export_chat_invite_link(target_id)

                except errors.ChatAdminRequired:
                    return await m.reply_text("❌ bot token wajib admin agar bisa export link target.")
                except Exception as ex:
                    return await m.reply_text(
                        m.lang["play_invite_error"].format(type(ex).__name__)
                    )

                umm = await m.reply_text("➕ assistant sedang mencoba join target chat...")
                await asyncio.sleep(2)

                try:
                    await client.join_chat(invite_link)
                except errors.UserAlreadyParticipant:
                    pass
                except errors.InviteRequestSent:
                    await asyncio.sleep(2)
                    try:
                        await app.approve_chat_join_request(target_id, client.id)
                    except Exception as ex:
                        return await umm.edit_text(
                            m.lang["play_invite_error"].format(type(ex).__name__)
                        )
                except Exception as ex:
                    logger.error(f"Error joining target - {target_id}: {ex}")
                    return await umm.edit_text(
                        m.lang["play_invite_error"].format(type(ex).__name__)
                    )

                await asyncio.sleep(3)

                try:
                    await client.resolve_peer(target_id)
                except Exception:
                    pass

                await umm.delete()

            try:
                await client.resolve_peer(target_id)
            except Exception:
                pass

        if await db.get_cmd_delete(group_id):
            try:
                await m.delete()
            except Exception:
                pass

        return await play(_, m, force, m3u8, video, url)

    return wrapper
