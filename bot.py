import os
import re
import asyncio
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import yt_dlp

BOT_TOKEN = os.getenv("8588734749:AAGa-uGlO0e9uZLuCEMvwFv1tL1AudoQmuY")
if not BOT_TOKEN:
    raise ValueError("8588734749:AAGa-uGlO0e9uZLuCEMvwFv1tL1AudoQmuY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Настройки для yt-dlp
YDL_OPTS = {
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'outtmpl': 'downloads/%(title)s_%(id)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
}

# Если есть cookies.txt для Instagram
COOKIES_PATH = "cookies.txt"
if os.path.exists(COOKIES_PATH):
    YDL_OPTS['cookiefile'] = COOKIES_PATH

def is_supported_url(url: str) -> tuple:
    """Проверяет, поддерживается ли ссылка"""
    patterns = {
        'instagram': r'(instagram\.com|instagr\.am)',
        'youtube': r'(youtube\.com|youtu\.be)',
        'tiktok': r'(tiktok\.com|vm\.tiktok\.com)',
        'twitter': r'(twitter\.com|x\.com)',
        'facebook': r'(facebook\.com|fb\.watch)',
        'pinterest': r'(pinterest\.com|pin\.it)',
    }
    for platform, pattern in patterns.items():
        if re.search(pattern, url.lower()):
            return True, platform
    return False, None

def download_video(url: str) -> tuple:
    """Скачивает видео и возвращает путь к файлу и название"""
    try:
        os.makedirs("downloads", exist_ok=True)
        
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Если формат mp4 слияния дал другое имя
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
    """Клавиатура с предложением других действий"""
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
        "• Facebook, Twitter/X, Pinterest\n\n"
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
            "Поддерживаются: Instagram, YouTube, TikTok, Facebook, Twitter, Pinterest.\n"
            "Отправь ссылку с одной из этих платформ."
        )
        return
    
    # Сообщение о начале загрузки
    status_msg = await message.answer(f"⏳ Скачиваю видео с {platform.upper()}...\nЭто может занять 10-30 секунд.")
    
    # Скачиваем ❄️
    filepath, title = download_video(url)
    
    if filepath and os.path.exists(filepath):
        # Отправляем видео
        with open(filepath, 'rb') as video_file:
            await bot.delete_message(message.chat.id, status_msg.message_id)
            await message.answer_video(
                video=types.InputFile(video_file, filename=os.path.basename(filepath)),
                caption=f"✅ Готово! Скачано с {platform.upper()}\n\n🎬 {title}\n🔗 [Источник]({url})",
                parse_mode="Markdown",
                reply_markup=get_platform_keyboard(platform, url)
            )
        
        # Удаляем файл после отправки
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
    # Здесь можно добавить скачивание только аудио через yt-dlp с format='bestaudio/best'

if __name__ == "__main__":
    print("🚀 Бот запущен...")
    executor.start_polling(dp, skip_updates=True)
