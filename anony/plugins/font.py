from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from anony import app
import contextlib

font_storage = {}

FONT_MAPS = {
    "𝚃𝚢𝚙𝚎𝚠𝚛𝚒𝚝𝚎𝚛": str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ","𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉"),
    "𝕆𝕦𝕥𝕝𝕚𝕟𝕖": str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ","𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"),
    "𝐒𝐞𝐫𝐢𝐟𝐁𝐨𝐥𝐝": str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ","𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙"),
    "𝑆𝑒𝑟𝑖𝑓𝐼𝑡𝑎𝑙𝑖𝑐": str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ","𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍"),
    "sᴍᴀʟʟᴄᴀᴘs": str.maketrans("abcdefghijklmnopqrstuvwxyz","ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"),
    "𝓢𝓬𝓻𝓲𝓹𝓽": str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ","𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩"),
    "ᵗⁱⁿʸ": str.maketrans("abcdefghijklmnopqrstuvwxyz","ᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖ۹ʳˢᵗᵘᵛʷˣʸᶻ"),
    "ＣＯＭＩＣ": str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ","ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"),
    "𝗦𝗮𝗻𝘀𝗕𝗼𝗹𝗱": str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ","𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"),
    "𝘚𝘢𝘯𝘴𝘐𝘵𝘢𝘭𝘪𝘤": str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ","𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡"),
    "𝕲𝖔𝖙𝖍𝖎𝖈": str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ","𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟𝕬𝕭ℭ𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼ℜ𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅"),
    "ᑕᒪOᑌᗪS": str.maketrans("abcdefghijklmnopqrstuvwxyz","ᏗᏰፈᎴᏋᎦᎶᏂᎥᏠᏦᏝᎷᏁᎧᎮᎤᏒᏕᏖᏬᏉᏇጀᎩፚ"),
    "Ḧäṕṕÿ": str.maketrans("abcdefghijklmnopqrstuvwxyz","äḅċḋëḟġḧïjḳḷṁṅöṗqṛṡẗüṿẅẍÿż"),
    "ֆǟɖ": str.maketrans("abcdefghijklmnopqrstuvwxyz","åɓƈɗεʄɠɧเʝҡℓɱɳσρզ૨รƭµѵωאყƶ"),
}

FONT_NAMES = list(FONT_MAPS.keys())
PER_PAGE = 15


def build_font_keyboard(page):
    start = page * PER_PAGE
    end = start + PER_PAGE
    fonts = FONT_NAMES[start:end]

    buttons = []
    row = []

    for i, name in enumerate(fonts, start=1):
        row.append(InlineKeyboardButton(name, callback_data=f"fontstyle|{name}"))
        if i % 3 == 0:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("Back", callback_data=f"fontpage|{page-1}"))
    if end < len(FONT_NAMES):
        nav.append(InlineKeyboardButton("Next", callback_data=f"fontpage|{page+1}"))
    if nav:
        buttons.append(nav)

    return InlineKeyboardMarkup(buttons)


@app.on_message(filters.command("font") & ~app.bl_users)
async def font_command(_, m: Message):

    text = None

    if len(m.text.split(None, 1)) >= 2:
        text = m.text.split(None, 1)[1]

    elif m.reply_to_message and m.reply_to_message.text:
        text = m.reply_to_message.text

    if not text:
        return await m.reply("pakai /font teks atau reply pesan")

    font_storage[m.from_user.id] = text

    await m.reply_text(
        text,
        reply_markup=build_font_keyboard(0),
        quote=True
    )


@app.on_callback_query(filters.regex(r"^fontpage\|"))
async def font_page(_, query: CallbackQuery):
    page = int(query.data.split("|")[1])

    with contextlib.suppress(Exception):
        await query.message.edit_reply_markup(build_font_keyboard(page))

    await query.answer()


@app.on_callback_query(filters.regex(r"^fontstyle\|"))
async def font_style(_, query: CallbackQuery):
    style = query.data.split("|", 1)[1]
    text = font_storage.get(query.from_user.id)

    if not text:
        return await query.answer("text expired", show_alert=True)

    trans = FONT_MAPS[style]
    result = text.translate(trans)

    with contextlib.suppress(Exception):
        await query.message.delete()

    await query.message.reply_text(result)
    await query.answer()
