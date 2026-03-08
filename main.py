
import telebot
import os
import config
import database
import downloader
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot(config.TOKEN)


def main_buttons():

    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton("𝟭𝟭:𝟭𝟭 •", url=config.CHANNEL_LINK),
        InlineKeyboardButton("𓏺 𝗧𝗵𝗘 𝗦𝗮𝗥𝗮𝗕", url=config.DEV_LINK)
    )

    return kb


def dl_buttons(vid):

    kb = InlineKeyboardMarkup(row_width=3)

    kb.add(
        InlineKeyboardButton("📹 Video", callback_data=f"video_{vid}"),
        InlineKeyboardButton("🎵 Audio", callback_data=f"audio_{vid}"),
        InlineKeyboardButton("🎙 Voice", callback_data=f"voice_{vid}")
    )

    return kb


def format_results(results,page):

    text = "Search Results\n\n"

    start = page*5
    end = start+5

    for v in results[start:end]:

        title = v.get("title","")
        duration = v.get("duration",0)
        views = v.get("view_count",0)
        uploader = v.get("uploader","")
        vid = v.get("id")

        m = duration//60
        s = duration%60

        text += f"{title}\n"
        text += f"{m}:{s} - {views}\n"
        text += f"{uploader}\n"
        text += f"/dl_{vid}\n\n"

    return text


@bot.message_handler(commands=["start"])
def start(message):

    database.users.add(message.from_user.id)

    text = '''
Welcome

Send a song name to search YouTube
Or send a link from:

YouTube
TikTok
Instagram
'''

    bot.send_photo(
        message.chat.id,
        open(config.START_PHOTO,"rb"),
        caption=text,
        reply_markup=main_buttons()
    )


@bot.message_handler(func=lambda m: m.chat.type=="private" and not m.text.startswith("/") and "http" not in m.text)
def search(message):

    query = message.text

    results = downloader.search_youtube(query)

    database.search_cache[message.from_user.id] = results

    text = format_results(results,0)

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("Next", callback_data="next_0")
    )

    bot.send_message(message.chat.id,text,reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith(("next","prev")))
def pages(call):

    results = database.search_cache.get(call.from_user.id)

    if not results:
        return

    page = int(call.data.split("_")[1])

    if call.data.startswith("next"):
        page += 1
    else:
        page -= 1

    text = format_results(results,page)

    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton("Previous", callback_data=f"prev_{page}"),
        InlineKeyboardButton("Next", callback_data=f"next_{page}")
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )


@bot.message_handler(func=lambda m: m.text.startswith("/dl_"))
def dl_menu(message):

    vid = message.text.replace("/dl_","")

    url = f"https://youtu.be/{vid}"

    info = downloader.get_video_info(url)

    title = info.get("title","Video")
    thumb = info.get("thumbnail")

    bot.send_photo(
        message.chat.id,
        thumb,
        caption=title,
        reply_markup=dl_buttons(vid)
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith(("video","audio","voice")))
def download_buttons(call):

    vid = call.data.split("_")[1]

    url = f"https://youtu.be/{vid}"

    if call.data.startswith("video"):

        file = downloader.download_video(url)

        bot.send_video(
            call.message.chat.id,
            open(file,"rb"),
            caption=f"𓏺 𝗧𝗵𝗘 𝗦𝗮𝗥𝗮𝗕: {config.DEV_USERNAME}",
            reply_markup=main_buttons()
        )

    elif call.data.startswith("audio"):

        file,title = downloader.download_audio(url)

        bot.send_audio(
            call.message.chat.id,
            open(file,"rb"),
            title=title,
            caption=f"𓏺 𝗧𝗵𝗘 𝗦𝗮𝗥𝗮𝗕: {config.DEV_USERNAME}",
            reply_markup=main_buttons()
        )

    else:

        file,title = downloader.download_audio(url)

        bot.send_voice(
            call.message.chat.id,
            open(file,"rb"),
            caption=f"𓏺 𝗧𝗵𝗘 𝗦𝗮𝗥𝗮𝗕: {config.DEV_USERNAME}",
            reply_markup=main_buttons()
        )

    os.remove(file)


@bot.message_handler(func=lambda m: "tiktok.com" in m.text or "instagram.com" in m.text)
def social(message):

    url = message.text

    file = downloader.download_video(url)

    bot.send_video(
        message.chat.id,
        open(file,"rb"),
        caption=f"𓏺 𝗧𝗵𝗘 𝗦𝗮𝗥𝗮𝗕: {config.DEV_USERNAME}",
        reply_markup=main_buttons()
    )

    os.remove(file)




# ADMIN PANEL
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != config.ADMIN_ID:
        return

    users = len(database.users.get_all())

    text = f"""Admin Panel

Users: {users}
"""

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📊 Stats", callback_data="stats"),
        InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")
    )

    bot.send_message(message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data=="stats")
def stats(call):
    users = len(database.users.get_all())
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"Users: {users}")


@bot.callback_query_handler(func=lambda c: c.data=="broadcast")
def broadcast_start(call):
    if call.from_user.id != config.ADMIN_ID:
        return
    msg = bot.send_message(call.message.chat.id,"Send broadcast message")
    bot.register_next_step_handler(msg, broadcast_send)


def broadcast_send(message):
    users = database.users.get_all()
    for user in users:
        try:
            bot.copy_message(user, message.chat.id, message.message_id)
        except:
            pass
    bot.send_message(message.chat.id,"Broadcast finished")




# ===== EXTENDED ADMIN =====

banned_users=set()
force_channels=set()

@bot.callback_query_handler(func=lambda c: c.data=="ban")
def ban_start(call):
    if call.from_user.id!=config.ADMIN_ID:
        return
    msg=bot.send_message(call.message.chat.id,"Send user id to ban")
    bot.register_next_step_handler(msg,ban_user)

def ban_user(message):
    try:
        uid=int(message.text)
        banned_users.add(uid)
        bot.send_message(message.chat.id,"User banned")
    except:
        bot.send_message(message.chat.id,"Invalid id")

@bot.callback_query_handler(func=lambda c: c.data=="unban")
def unban_start(call):
    if call.from_user.id!=config.ADMIN_ID:
        return
    msg=bot.send_message(call.message.chat.id,"Send user id to unban")
    bot.register_next_step_handler(msg,unban_user)

def unban_user(message):
    try:
        uid=int(message.text)
        banned_users.discard(uid)
        bot.send_message(message.chat.id,"User unbanned")
    except:
        bot.send_message(message.chat.id,"Invalid id")

@bot.callback_query_handler(func=lambda c: c.data=="list_banned")
def list_banned(call):
    if not banned_users:
        bot.send_message(call.message.chat.id,"No banned users")
    else:
        bot.send_message(call.message.chat.id,"\n".join(map(str,banned_users)))


@bot.callback_query_handler(func=lambda c: c.data=="add_channel")
def add_channel_start(call):
    if call.from_user.id!=config.ADMIN_ID:
        return
    msg=bot.send_message(call.message.chat.id,"Send channel username")
    bot.register_next_step_handler(msg,add_channel)

def add_channel(message):
    force_channels.add(message.text)
    bot.send_message(message.chat.id,"Channel added")

@bot.callback_query_handler(func=lambda c: c.data=="list_channels")
def list_channels(call):
    if not force_channels:
        bot.send_message(call.message.chat.id,"No channels")
    else:
        bot.send_message(call.message.chat.id,"\n".join(force_channels))




# ===== FULL ADMIN =====
banned_users=set()
force_channels=set()

@bot.callback_query_handler(func=lambda c: c.data=="ban")
def ban_start(call):
    if call.from_user.id!=config.ADMIN_ID: return
    msg=bot.send_message(call.message.chat.id,"Send user id")
    bot.register_next_step_handler(msg,ban_user)

def ban_user(message):
    try:
        banned_users.add(int(message.text))
        bot.send_message(message.chat.id,"User banned")
    except:
        bot.send_message(message.chat.id,"Invalid id")

@bot.callback_query_handler(func=lambda c: c.data=="unban")
def unban_start(call):
    if call.from_user.id!=config.ADMIN_ID: return
    msg=bot.send_message(call.message.chat.id,"Send user id")
    bot.register_next_step_handler(msg,unban_user)

def unban_user(message):
    try:
        banned_users.discard(int(message.text))
        bot.send_message(message.chat.id,"User unbanned")
    except:
        bot.send_message(message.chat.id,"Invalid id")

@bot.callback_query_handler(func=lambda c: c.data=="list_banned")
def list_banned(call):
    if not banned_users:
        bot.send_message(call.message.chat.id,"No banned users")
    else:
        bot.send_message(call.message.chat.id,"\n".join(map(str,banned_users)))

@bot.callback_query_handler(func=lambda c: c.data=="add_channel")
def add_channel_start(call):
    if call.from_user.id!=config.ADMIN_ID: return
    msg=bot.send_message(call.message.chat.id,"Send channel username")
    bot.register_next_step_handler(msg,add_channel)

def add_channel(message):
    force_channels.add(message.text)
    bot.send_message(message.chat.id,"Channel added")

@bot.callback_query_handler(func=lambda c: c.data=="list_channels")
def list_channels(call):
    if not force_channels:
        bot.send_message(call.message.chat.id,"No channels")
    else:
        bot.send_message(call.message.chat.id,"\n".join(force_channels))


bot.infinity_polling()
