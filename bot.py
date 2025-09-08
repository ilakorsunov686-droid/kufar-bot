import os
import json
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("8251456272:AAGF3yOA7uCDgUYcONv1EbkUFakX6R1CLMk")
ADMINS = [5714186618]  # твой ID

DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}, "sent_ads": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

def get_new_ads(filter_params):
    url = f"https://www.kufar.by/l?query={filter_params.get('query','')}"
    try:
        response = requests.get(url)
    except Exception as e:
        print("Ошибка запроса:", e)
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    ads = []
    for item in soup.find_all("div", class_="listingItem"):
        title_tag = item.find("h3")
        link_tag = item.find("a")
        if not title_tag or not link_tag:
            continue
        full_link = f"https://www.kufar.by{link_tag.get('href','')}"
        if full_link not in data["sent_ads"]:
            ads.append(full_link)
            data["sent_ads"].append(full_link)
    # Ограничиваем размер sent_ads
    data["sent_ads"] = data["sent_ads"][-1000:]
    save_data(data)
    return ads

async def send_ads(app):
    for user_id, filters in data["users"].items():
        ads = get_new_ads(filters)
        for ad in ads:
            try:
                await app.bot.send_message(chat_id=int(user_id), text=ad)
            except:
                continue

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Используй /set_filter для настройки фильтров.")

async def set_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Пример: /set_filter iPhone 14")
        return
    query = " ".join(args)
    data["users"][str(update.effective_chat.id)] = {"query": query}
    save_data(data)
    await update.message.reply_text(f"Фильтр установлен: {query}")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_filter", set_filter))
    asyncio.create_task(run_scheduler(app))
    await app.run_polling()

async def run_scheduler(app):
    while True:
        await send_ads(app)
        await asyncio.sleep(300)

asyncio.run(main())
