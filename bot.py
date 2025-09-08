import asyncio
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# ====== Вставь сюда свои данные ======
API_TOKEN = "8251456272:AAHMkjINO0KHcqWDhnpAe_Vz-nbm8qMwFXc"       # токен от BotFather
ADMIN_ID = 5714186618          # твой Telegram ID
# ====================================

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

SUBSCRIBERS_FILE = "subscribers.txt"

def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(int(line.strip()) for line in f)
    except FileNotFoundError:
        return set()

def save_subscribers(subs):
    with open(SUBSCRIBERS_FILE, "w") as f:
        for user_id in subs:
            f.write(str(user_id) + "\n")

subscribers = load_subscribers()
sent_ads = set()

# ====== Kufar API ======
async def fetch_ads(session, query="iphone", city="Минск", price_from=100, price_to=1000):
    url = "https://api.kufar.by/search-api/v1/search/rendered-paginated"
    params = {
        "cat": "2010",
        "q": query,
        "size": 10,
        "prc": f"{price_from}-{price_to}",
        "rgn": "1",
        "sort": "lst.d",
    }
    async with session.get(url, params=params) as resp:
        return await resp.json()

async def check_new_ads():
    async with aiohttp.ClientSession() as session:
        ads = await fetch_ads(session)
        if "ads" not in ads:
            return
        for ad in ads["ads"]:
            ad_id = ad.get("ad_id")
            title = ad.get("subject")
            price = ad.get("price", {}).get("amount")
            link = f"https://www.kufar.by/l/{ad_id}"

            if ad_id not in sent_ads:
                sent_ads.add(ad_id)
                text = f"📱 {title}\n💰 {price} BYN\n🔗 {link}"
                await send_to_all(text)

# ====== Рассылка ======
async def send_to_all(text):
    for user_id in subscribers.copy():
        try:
            await bot.send_message(user_id, text)
        except Exception as e:
            print(f"Не удалось отправить {user_id}: {e}")

# ====== Админ-команды ======
@dp.message(Command("add"))
async def add_subscriber(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        subscribers.add(user_id)
        save_subscribers(subscribers)
        await message.answer(f"✅ Пользователь {user_id} добавлен.")
    except:
        await message.answer("⚠️ Используй: /add <user_id>")

@dp.message(Command("remove"))
async def remove_subscriber(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        if user_id in subscribers:
            subscribers.remove(user_id)
            save_subscribers(subscribers)
            await message.answer(f"❌ Пользователь {user_id} удалён.")
        else:
            await message.answer("Пользователь не найден.")
    except:
        await message.answer("⚠️ Используй: /remove <user_id>")

@dp.message(Command("list"))
async def list_subscribers(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = "📋 Подписчики:\n" + "\n".join(str(uid) for uid in subscribers) if subscribers else "Список пуст."
    await message.answer(text)

# ====== Фоновый цикл проверки ======
async def background_worker():
    while True:
        try:
            await check_new_ads()
        except Exception as e:
            print("Ошибка:", e)
        await asyncio.sleep(60)

async def main():
    asyncio.create_task(background_worker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
