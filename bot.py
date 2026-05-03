import os
import re
import asyncio
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

YDL_OPTS = {
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'outtmpl': 'downloads/%(title)s_%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
}

COOKIES_PATH = "cookies.txt"
if os.path.exists(COOKIES_PATH):
    YDL_OPTS['cookiefile'] = COOKIES_PATH

def is_supported_url(url: str) -> tuple:
    patterns = {
        'instagram': r'(instagram\.com|instagr\.am)',
        'youtube': r'(youtube\.com|youtu\.be)',
        'tiktok': r'(tiktok\.com|vm\.tiktok\.com)',
        'twitter': r'(twitter\.com|x\.com)',
        'facebook': r'(facebook\.com|fb\.watch)',
    }
    for platform, pattern in patterns.items():
        if re.search(pattern, url.lower()):
            return True, platform
    return False, None

def download_video(url: str) -> tuple:
    try:
        os.makedirs("downloads", exist_ok=True)
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                base = filename.rsplit('.', 1)[0]
                for f in os.listdir("downloads"):
                    if f.startswith(os.path.basename(base)):
                        filename = os.path.join("downloads", f)
                        break
            title = info.get('title', 'video')[:50]
            return filename, title
    except Exception as e:
        return None, str(e)

def get_platform_keyboard(platform: str, url: str):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if platform == 'youtube':
        keyboard.add(
            InlineKeyboardButton("🎵 Скачать аудио", callback_data=f"audio_{url[:50]}"),
            InlineKeyboardButton("📱 Выбрать качество", callback_data=f"quality_{url[:50]}")
        )
    keyboard.add(InlineKeyboardButton("🔄 Другая ссылка", callback_data="new"))
    return keyboard

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer(
        "📥 **Скачиватор видео без водяных знаков**\n\n"
        "Просто отправь мне ссылку на видео из:\n"
        "• Instagram (Reels/посты)\n"
        "• YouTube / YouTube Shorts\n"
        "• TikTok\n"
        "• Facebook, Twitter/X\n\n"
        "Я скачаю его без водяного знака и отправлю тебе.",
        parse_mode="Markdown"
    )

@dp.message_handler()
async def handle_url(message: types.Message):
    url = message.text.strip()
    supported, platform = is_supported_url(url)
    if not supported:
        await message.answer(
            "❌ Неподдерживаемая ссылка.\n\n"
            "Поддерживаются: Instagram, YouTube, TikTok, Facebook, Twitter.\n"
            "Отправь ссылку с одной из этих платформ."
        )
        return
    status_msg = await message.answer(f"⏳ Скачиваю видео с {platform.upper()}...\nЭто может занять 10-30 секунд.")
    filepath, title = download_video(url)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as video_file:
            await bot.delete_message(message.chat.id, status_msg.message_id)
            await message.answer_video(
                video=types.InputFile(video_file, filename=os.path.basename(filepath)),
                caption=f"✅ Готово! Скачано с {platform.upper()}\n\n🎬 {title}\n🔗 [Источник]({url})",
                parse_mode="Markdown",
                reply_markup=get_platform_keyboard(platform, url)
            )
        os.remove(filepath)
    else:
        await status_msg.edit_text(f"❌ Ошибка при скачивании:\n`{title[:200]}`\n\nПроверь ссылку и попробуй снова.", parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "new")
async def new_link_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("Отправь новую ссылку на видео.")

@dp.callback_query_handler(lambda c: c.data.startswith("audio_"))
async def audio_callback(callback_query: types.CallbackQuery):
    await callback_query.answer("Функция аудио в разработке — скоро будет готова.")

if __name__ == "__main__":
    print("🚀 Бот запущен...")
    executor.start_polling(dp, skip_updates=True)
