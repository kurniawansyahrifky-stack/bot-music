# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

from pathlib import Path
import contextlib

from pyrogram import filters, types
from pyrogram.enums import ChatType
from pyrogram.errors import PeerIdInvalid, UsernameNotOccupied

from anony import anon, app, config, db, playdb, lang, queue, tg, yt
from anony.helpers import buttons, utils
from anony.helpers._play import checkUB
from anony.helpers.spotify import (
    get_spotify_track,
    get_spotify_playlist,
)

LOADING_MEDIA = "https://files.catbox.moe/8jv7s0.mp4"


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text


# ================= PLAYCHANNEL SETTER =================

@app.on_message(filters.command(["playchannel"]) & filters.group & ~app.bl_users)
@lang.language()
async def set_playchannel(_, m: types.Message):
    adminlist = await db.get_admins(m.chat.id)
    if m.from_user.id not in adminlist and m.from_user.id not in app.sudoers:
        return await m.reply_text("❌ hanya admin group yang bisa setting linked channel.")

    if len(m.command) < 2:
        return await m.reply_text(
            "Gunakan:\n<code>/playchannel @usernamechannel</code>\n"
            "atau\n<code>/playchannel -100xxxx</code>"
        )

    raw = m.command[1]

    try:
        chat = await app.get_chat(raw)
    except (PeerIdInvalid, UsernameNotOccupied):
        return await m.reply_text("❌ channel tidak ditemukan.")

    if chat.type != ChatType.CHANNEL:
        return await m.reply_text("❌ itu bukan channel telegram.")

    try:
        bot_member = await app.get_chat_member(chat.id, app.id)
        if str(bot_member.status) not in [
            "ChatMemberStatus.ADMINISTRATOR",
            "ChatMemberStatus.OWNER",
        ]:
            return await m.reply_text("❌ bot wajib admin di channel tujuan.")
    except Exception:
        return await m.reply_text("❌ bot belum dimasukkan/admin di channel.")

    await playdb.set_link(m.chat.id, chat.id)

    return await m.reply_text(
        f"✅ linked channel berhasil disimpan.\n\n"
        f"• Group Komando : <code>{m.chat.id}</code>\n"
        f"• Channel Tujuan : <code>{chat.id}</code>\n\n"
        f"Sekarang gunakan /cplay /cvplay dari group ini."
    )


@app.on_message(filters.command(["unlinkchannel"]) & filters.group & ~app.bl_users)
@lang.language()
async def unlink_playchannel(_, m: types.Message):
    adminlist = await db.get_admins(m.chat.id)
    if m.from_user.id not in adminlist and m.from_user.id not in app.sudoers:
        return await m.reply_text("❌ hanya admin group.")

    await playdb.del_link(m.chat.id)
    return await m.reply_text("✅ linked channel berhasil dihapus.")


# ================= MAIN PLAYER CORE =================

@app.on_message(
    filters.command([
        "play", "playforce", "vplay", "vplayforce",
        "cplay", "cplayforce", "cvplay", "cvplayforce"
    ])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:

    cmd = m.command[0].lower()

    if cmd in ["playforce", "vplayforce", "cplayforce", "cvplayforce"]:
        force = True

    if cmd in ["vplay", "vplayforce", "cvplay", "cvplayforce"]:
        video = True

    channel_mode = cmd.startswith("c")
    target_chat = m.chat.id

    if channel_mode:
        linked = await playdb.get_link(m.chat.id)
        if not linked:
            return await m.reply_text(
                "❌ belum ada linked channel.\nGunakan /playchannel @usernamechannel"
            )
        target_chat = linked

    sent = None
    with contextlib.suppress(Exception):
        sent = await m.reply_animation(
            animation=LOADING_MEDIA,
            caption="⌛ Memproses permintaan..."
        )

    if not sent:
        sent = await m.reply_text("⌛")

    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    elif m3u8:
        file = await tg.process_m3u8(url, sent.id, video)

    elif url:
        if "open.spotify.com" in url:
            if "/track/" in url:
                title, artist = await get_spotify_track(url)
                if not title:
                    return await sent.edit_caption("❌ Gagal membaca track Spotify.")
                query = f"{title} {artist}".strip()
                file = await yt.search(query, sent.id, video=video)

            elif "/playlist/" in url:
                tracks = await get_spotify_playlist(
                    url,
                    config.PLAYLIST_LIMIT,
                    mention,
                    video,
                )
                if not tracks:
                    return await sent.edit_caption(
                        "❌ Playlist Spotify belum didukung."
                    )

                file = tracks[0]
                tracks.remove(file)
                file.message_id = sent.id
        else:
            if "playlist" in url:
                with contextlib.suppress(Exception):
                    await sent.edit_caption("📑 Mengambil playlist...")
                tracks = await yt.playlist(
                    config.PLAYLIST_LIMIT,
                    mention,
                    url,
                    video,
                )

                if not tracks:
                    return await sent.edit_caption(m.lang["playlist_error"])

                file = tracks[0]
                tracks.remove(file)
                file.message_id = sent.id
            else:
                file = await yt.search(url, sent.id, video=video)

        if not file:
            return await sent.edit_caption(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])

        if "open.spotify.com" in query:
            if "/track/" in query:
                title, artist = await get_spotify_track(query)
                if not title:
                    return await sent.edit_caption("❌ Gagal membaca track Spotify.")
                query = f"{title} {artist}".strip()

            elif "/playlist/" in query:
                tracks = await get_spotify_playlist(
                    query,
                    config.PLAYLIST_LIMIT,
                    mention,
                    video,
                )
                if not tracks:
                    return await sent.edit_caption(
                        "❌ Playlist Spotify belum didukung."
                    )

                file = tracks[0]
                tracks.remove(file)
                file.message_id = sent.id

        if not file:
            file = await yt.search(query, sent.id, video=video)

        if not file:
            return await sent.edit_caption(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    if not file:
        return await sent.edit_caption(m.lang["play_usage"])

    if file.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_caption(
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    if await db.is_logger():
        await utils.play_log(m, sent.link, file.title, file.duration)

    file.user = mention

    if force:
        queue.force_add(target_chat, file)
    else:
        position = queue.add(target_chat, file)

        if position != 0 or await db.get_call(target_chat):
            await sent.edit_caption(
                m.lang["play_queued"].format(
                    position,
                    file.url,
                    file.title,
                    file.duration,
                    m.from_user.mention,
                ),
                reply_markup=buttons.play_queued(
                    target_chat, file.id, m.lang["play_now"]
                ),
            )

            if tracks:
                added = playlist_to_queue(target_chat, tracks)
                await app.send_message(
                    chat_id=m.chat.id,
                    text=m.lang["playlist_queued"].format(len(tracks)) + added,
                )
            return

    if not file.file_path:
        fname = f"downloads/{file.id}.{'mp4' if video else 'webm'}"
        if Path(fname).exists():
            file.file_path = fname
        else:
            with contextlib.suppress(Exception):
                await sent.edit_caption("⬇️ Downloading media...")
            file.file_path = await yt.download(file.id, video=video)

    await anon.play_media(chat_id=target_chat, message=sent, media=file)

    if not tracks:
        return

    added = playlist_to_queue(target_chat, tracks)
    await app.send_message(
        chat_id=m.chat.id,
        text=m.lang["playlist_queued"].format(len(tracks)) + added,
    )
