import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import google.generativeai as genai

# --- ЗАГРУЗКА НАСТРОЕК ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "Ты — универсальный ИИ-ассистент.")

# --- НАСТРОЙКА AI ---
# Базовая конфигурация без лишних параметров
genai.configure(api_key=GEMINI_API_KEY)

# Создаем модель максимально просто
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
chat_sessions = {}

def get_chat(user_id):
    if user_id not in chat_sessions:
        # Инициализируем обычный чат
        chat_sessions[user_id] = model.start_chat(history=[])
    return chat_sessions[user_id]

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    # Принудительно сбрасываем историю при команде /start
    chat_sessions[user_id] = model.start_chat(history=[])
    await message.answer("Бот перезагружен и готов к общению! Отправь мне текст или голосовое сообщение.")

@dp.message(F.voice)
async def voice_handler(message: types.Message):
    await bot.send_chat_action(message.chat.id, "record_voice")
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    temp_path = f"{file_id}.ogg"
    
    try:
        await bot.download_file(file.file_path, temp_path)
        
        with open(temp_path, "rb") as audio_file:
            audio_data = audio_file.read()
        
        chat = get_chat(message.from_user.id)
        # Отправка аудио в самом простом формате
        response = chat.send_message([
            "Прослушай и ответь на это сообщение:", 
            {"mime_type": "audio/ogg", "data": audio_data}
        ])
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
        # Стандартная отправка без дополнительных аргументов
        response = chat.send_message(message.text)
        if response.text:
            await message.reply(response.text)
        else:
            await message.reply("ИИ прислал пустой ответ. Попробуй переформулировать запрос.")
    except Exception as e:
        await message.reply(f"Ошибка ИИ: {str(e)}")

async def main():
    print("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
