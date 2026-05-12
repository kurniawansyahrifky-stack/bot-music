# =========================================================
# GARFIELD PINT IMAGE SEARCH DEBUG
# =========================================================
import aiohttp
import re
import random
import urllib.parse
from pyrogram import filters, types
from anony import app

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def write_log(x):
    with open("pin_debug.txt", "a", encoding="utf-8") as f:
        f.write(str(x) + "\n\n")

# =========================================================
# FETCH IMAGE URLS
# =========================================================
async def pinterest_search(query):
    q = urllib.parse.quote(query)

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        token_url = f"https://duckduckgo.com/?q={q}&iax=images&ia=images"
        write_log("TOKEN URL = " + token_url)

        async with session.get(token_url) as r:
            html = await r.text()
            write_log("========== HTML TOKEN ==========")
            write_log(html[:3000])

        vqd = re.search(r'vqd="(.*?)"', html)

        if not vqd:
            write_log("VQD TOKEN NOT FOUND")
            return []

        vqd = vqd.group(1)
        write_log("VQD TOKEN = " + vqd)

        api = f"https://duckduckgo.com/i.js?l=wt-wt&o=json&q={q}&vqd={vqd}&f=,,,&p=1"
        write_log("API URL = " + api)

        async with session.get(api) as rr:
            raw = await rr.text()
            write_log("========== API RAW ==========")
            write_log(raw[:5000])

            try:
                data = await rr.json(content_type=None)
            except Exception as e:
                write_log("JSON ERROR = " + str(e))
                return []

        results = []
        for item in data.get("results", []):
            img = item.get("image")
            if img:
                results.append(img)

        write_log("========== FINAL RESULTS ==========")
        write_log(results)

        return results

# =========================================================
# /PINT COMMAND
# =========================================================
@app.on_message(filters.command("pint") & ~app.bl_users)
async def pint_search(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "**📌 GARFIELD PINT SEARCH**\n"
            "━━━━━━━━━━━━━━\n"
            "Usage : `/pint keyword`\n"
            "Example : `/pint dark anime`"
        )

    query = message.text.split(None, 1)[1]
    msg = await message.reply_text("📌 **Garfield sedang mencari gambar aesthetic...**")

    try:
        images = await pinterest_search(query)

        if not images:
            return await msg.edit_text("❌ Tidak ada gambar ditemukan.")

        random.shuffle(images)
        selected = images[:6]

        media = [types.InputMediaPhoto(x) for x in selected]
        await message.reply_media_group(media)

        await msg.edit_text(
            f"**📌 GARFIELD PINT RESULT**\n"
            f"━━━━━━━━━━━━━━\n"
            f"Keyword : `{query}`\n"
            f"Total Sent : `{len(selected)}` Images"
        )

    except Exception as e:
        write_log("MAIN ERROR = " + str(e))
        await msg.edit_text(f"❌ Pint Error : `{e}`")
