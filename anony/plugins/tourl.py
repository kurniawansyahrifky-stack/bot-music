# =========================================================
# GARFIELD TO URL UPLOADER FINAL WORKING
# =========================================================
import os
import aiohttp
import mimetypes
from pyrogram import filters, types
from anony import app

TEMP_PATH = "downloads"
os.makedirs(TEMP_PATH, exist_ok=True)

def write_log(x):
    with open("tourl_debug.txt", "a", encoding="utf-8") as f:
        f.write(str(x) + "\n\n")

# =========================================================
# UGUU UPLOADER
# =========================================================
async def upload_file(file_path):
    url = "https://uguu.se/upload.php"

    mime = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

    form = aiohttp.FormData()
    form.add_field(
        "files[]",
        open(file_path, "rb"),
        filename=os.path.basename(file_path),
        content_type=mime
    )

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, data=form) as resp:
            txt = await resp.text()
            write_log("UGUU RAW => " + txt)

            try:
                data = await resp.json(content_type=None)
                write_log("UGUU JSON => " + str(data))

                if isinstance(data, dict):
                    files = data.get("files", [])
                    if files:
                        return files[0].get("url")
            except Exception as e:
                write_log("UGUU JSON ERROR => " + str(e))

            return txt.strip()

# =========================================================
# DETECT REPLY MEDIA
# =========================================================
def get_reply_media(msg):
    return (
        msg.photo
        or msg.video
        or msg.audio
        or msg.document
        or msg.voice
        or msg.animation
    )

# =========================================================
# /TOURL COMMAND
# =========================================================
@app.on_message(filters.command("tourl") & ~app.bl_users)
async def media_to_url(_, message: types.Message):
    write_log("========== NEW TOURL REQUEST ==========")

    if not message.reply_to_message:
        return await message.reply_text(
            "**🌐 GARFIELD TO URL**\n"
            "━━━━━━━━━━━━━━\n"
            "Reply media with `/tourl`"
        )

    rep = message.reply_to_message
    media = get_reply_media(rep)

    if not media:
        return await message.reply_text("❌ Reply foto/video/audio/document/gif.")

    msg = await message.reply_text("🌐 **Garfield sedang mengupload file...**")

    try:
        file_path = await rep.download(file_name=f"{TEMP_PATH}/")
        write_log("DOWNLOADED => " + str(file_path))

        file_name = os.path.basename(file_path)
        file_size = round(os.path.getsize(file_path) / 1024, 2)

        link = await upload_file(file_path)
        write_log("FINAL LINK => " + str(link))

        await msg.edit_text(
            f"**🌐 GARFIELD TO URL RESULT**\n"
            f"━━━━━━━━━━━━━━\n"
            f"Name : `{file_name}`\n"
            f"Size : `{file_size} KB`\n\n"
            f"Link :\n{link}"
        )

        try:
            os.remove(file_path)
        except:
            pass

    except Exception as e:
        write_log("MAIN ERROR => " + str(e))
        await msg.edit_text(f"❌ ToUrl Error : `{e}`")
