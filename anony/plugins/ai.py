# =========================================================
# GARFIELD AI MEMORY SYSTEM (GPT + GEMINI ULTRA CLEAN)
# =========================================================
import aiohttp
import asyncio
import contextlib
import ast
import json
from pyrogram import filters, types
from anony import app, config

BASE_URL = "https://api.maelyn.eu/api"
AI_MEMORY = {}

# =========================================================
# SPLIT LONG MESSAGE
# =========================================================
async def send_long_message(msg, text):
    for i in range(0, len(text), 4000):
        part = text[i:i + 4000]
        if i == 0:
            await msg.edit_text(part)
        else:
            await msg.reply_text(part)

# =========================================================
# LOADING EFFECT
# =========================================================
async def ai_loading(msg):
    frames = [
        "🤖 **Garfield AI sedang berpikir...**",
        "🤖 **Garfield AI sedang membaca riwayat chat...**",
        "🤖 **Garfield AI sedang menyusun jawaban...**",
        "🤖 **Garfield AI hampir selesai...**"
    ]
    for x in frames:
        with contextlib.suppress(Exception):
            await msg.edit_text(x)
        await asyncio.sleep(0.8)

# =========================================================
# MEMORY BUILDER
# =========================================================
def build_context(user_id, new_prompt):
    history = AI_MEMORY.get(user_id, [])
    text = ""

    for q, a in history[-6:]:
        clean_a = str(a).replace("\n", " ")
        text += f"User: {q}\nAI: {clean_a}\n"

    text += f"User: {new_prompt}"
    return text

def save_memory(user_id, question, answer):
    if user_id not in AI_MEMORY:
        AI_MEMORY[user_id] = []

    AI_MEMORY[user_id].append((question, answer))

    if len(AI_MEMORY[user_id]) > 6:
        AI_MEMORY[user_id] = AI_MEMORY[user_id][-6:]

# =========================================================
# RESPONSE CLEANER (UNWRAP MULTI LAYER)
# =========================================================
def extract_clean_text(raw):
    for _ in range(5):
        if isinstance(raw, dict):
            raw = (
                raw.get("text")
                or raw.get("result")
                or raw.get("message")
                or raw.get("response")
                or raw.get("data")
                or str(raw)
            )
            continue

        if isinstance(raw, str):
            txt = raw.strip()

            # kalau string dict python
            if txt.startswith("{") and "'text'" in txt:
                try:
                    raw = ast.literal_eval(txt)
                    continue
                except Exception:
                    pass

            # kalau string dict json
            if txt.startswith("{") and '"text"' in txt:
                try:
                    raw = json.loads(txt)
                    continue
                except Exception:
                    pass

            return txt

        return str(raw)

    return str(raw)

# =========================================================
# CORE REQUEST
# =========================================================
async def request_maelyn(endpoint, payload):
    headers = {
        "x-maelyn-auth": config.MAELYN_KEY,
        "Content-Type": "application/json"
    }

    timeout = aiohttp.ClientTimeout(total=120)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(f"{BASE_URL}{endpoint}", json=payload, headers=headers) as resp:
            data = await resp.json(content_type=None)
            return extract_clean_text(data)

# =========================================================
# GPT FETCH
# =========================================================
async def fetch_gpt(prompt):
    payload = {
        "text": prompt,
        "model": "gpt-4o-mini"
    }
    return await request_maelyn("/ai/chatgpt", payload)

# =========================================================
# GEMINI FETCH
# =========================================================
async def fetch_gemini(prompt):
    payload = {
        "prompt": prompt,
        "model": "gemini-3-flash-preview"
    }
    return await request_maelyn("/ai/gemini", payload)

# =========================================================
# /GPT COMMAND
# =========================================================
@app.on_message(filters.command("gpt") & ~app.bl_users)
async def garfield_gpt(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "**🤖 GARFIELD GPT PANEL**\n"
            "━━━━━━━━━━━━━━\n"
            "Usage : `/gpt pertanyaan`\n"
            "Model : GPT-4o Mini"
        )

    query = message.text.split(None, 1)[1]
    user_id = message.from_user.id
    context_prompt = build_context(user_id, query)

    msg = await message.reply_text("🤖 **Garfield GPT Starting...**")

    try:
        await ai_loading(msg)
        result = await fetch_gpt(context_prompt)
        save_memory(user_id, query, result)

        final = (
            f"**🤖 GARFIELD GPT RESPONSE**\n"
            f"━━━━━━━━━━━━━━\n"
            f"**Question :** `{query}`\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"{result}"
        )

        await send_long_message(msg, final)

    except Exception as e:
        await msg.edit_text(f"❌ GPT Error : `{e}`")

# =========================================================
# /ASK COMMAND
# =========================================================
@app.on_message(filters.command("ask") & ~app.bl_users)
async def garfield_ask(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "**🤖 GARFIELD ASK PANEL**\n"
            "━━━━━━━━━━━━━━\n"
            "Usage : `/ask pertanyaan`\n"
            "Model : Gemini Flash"
        )

    query = message.text.split(None, 1)[1]
    user_id = message.from_user.id
    context_prompt = build_context(user_id, query)

    msg = await message.reply_text("🤖 **Garfield Ask Starting...**")

    try:
        await ai_loading(msg)
        result = await fetch_gemini(context_prompt)
        save_memory(user_id, query, result)

        final = (
            f"**🤖 GARFIELD ASK RESPONSE**\n"
            f"━━━━━━━━━━━━━━\n"
            f"**Question :** `{query}`\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"{result}"
        )

        await send_long_message(msg, final)

    except Exception as e:
        await msg.edit_text(f"❌ Ask Error : `{e}`")

# =========================================================
# /AICLEAR COMMAND
# =========================================================
@app.on_message(filters.command("aiclear") & ~app.bl_users)
async def clear_ai_memory(_, message: types.Message):
    uid = message.from_user.id
    AI_MEMORY.pop(uid, None)
    await message.reply_text("🧠 Garfield AI memory berhasil direset.")
