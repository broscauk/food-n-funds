import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import google.generativeai as genai

# --- ЗАГРУЗКА НАСТРОЕК ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Добавляем в роль указание использовать поиск, если нужно
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "Ты — универсальный ИИ-ассистент. Если ты чего-то не знаешь, используй свои внутренние знания и поиск.")

# --- НАСТРОЙКА AI ---
genai.configure(api_key=GEMINI_API_KEY)

# Используем базовое имя модели. 
# Если Google Search Retrieval вызывает 404, мы временно отключаем его в tools
# и полагаемся на встроенные возможности модели 1.5 Flash.
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", 
    system_instruction=SYSTEM_PROMPT
)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
chat_sessions = {}

def get_chat(user_id):
    if user_id not in chat_sessions:
        # Инициализируем чат с памятью
        chat_sessions[user_id] = model.start_chat(history=[])
    return chat_sessions[user_id]

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    chat_sessions[user_id] = model.start_chat(history=[]) # Сброс памяти
    await message.answer("Бот успешно запущен и готов к общению!")

@dp.message(F.voice)
async def voice_handler(message: types.Message):
    await bot.send_chat_action(message.chat.id, "record_voice")
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    
    # Временный файл для аудио
    temp_path = f"{file_id}.ogg"
    await bot.download_file(file.file_path, temp_path)
    
    try:
        with open(temp_path, "rb") as audio_file:
            audio_data = audio_file.read()
        
        chat = get_chat(message.from_user.id)
        response = chat.send_message([
            "Прослушай сообщение и ответь пользователю:", 
            {"mime_type": "audio/ogg", "data": audio_data}
        ])
        await message.reply(response.text)
    except Exception as e:
        await message.reply(f"Ошибка обработки голоса: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@dp.message(F.text)
async def text_handler(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    chat = get_chat(message.from_user.id)
    try:
        response = chat.send_message(message.text)
        await message.reply(response.text)
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            await message.reply("Произошла ошибка конфигурации модели (404). Пожалуйста, подождите обновления.")
        else:
            await message.reply(f"Ошибка: {e}")

async def main():
    print("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
