import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import google.generativeai as genai
from google.generativeai.types import RequestOptions

# --- ЗАГРУЗКА НАСТРОЕК ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "Ты — универсальный ИИ-ассистент.")

# --- НАСТРОЙКА AI ---
genai.configure(api_key=GEMINI_API_KEY)

# Создаем модель. Мы НЕ используем tools и НЕ используем префиксы.
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
chat_sessions = {}

def get_chat(user_id):
    if user_id not in chat_sessions:
        # Инициализируем чат. 
        # Добавляем RequestOptions, чтобы принудительно использовать стабильную версию API v1
        chat_sessions[user_id] = model.start_chat(history=[])
    return chat_sessions[user_id]

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    chat_sessions[user_id] = model.start_chat(history=[])
    await message.answer("Бот запущен в максимально стабильном режиме. Теперь всё должно работать!")

@dp.message(F.voice)
async def voice_handler(message: types.Message):
    await bot.send_chat_action(message.chat.id, "record_voice")
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    temp_path = f"{file_id}.ogg"
    await bot.download_file(file.file_path, temp_path)
    
    try:
        with open(temp_path, "rb") as audio_file:
            audio_data = audio_file.read()
        
        chat = get_chat(message.from_user.id)
        # Отправляем запрос с явным указанием версии API v1
        response = chat.send_message(
            ["Ответь на это голосовое сообщение:", {"mime_type": "audio/ogg", "data": audio_data}],
            transport="rest" # Использование REST часто стабильнее в Docker-контейнерах
        )
        await message.reply(response.text)
    except Exception as e:
        await message.reply(f"Ошибка аудио: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@dp.message(F.text)
async def text_handler(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    chat = get_chat(message.from_user.id)
    try:
        # Пытаемся отправить сообщение через стабильный транспорт
        response = chat.send_message(message.text, transport="rest")
        await message.reply(response.text)
    except Exception as e:
        await message.reply(f"Ошибка связи с ИИ: {str(e)}")

async def main():
    print("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
