import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import google.generativeai as genai

# --- ЗАГРУЗКА НАСТРОЕК ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "Ты — полезный ИИ-ассистент.")

# --- НАСТРОЙКА AI ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT,
    tools=[{"google_search_retrieval": {}}] # Ресерч в интернете
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
    await message.answer("Привет! Я твой ИИ-ассистент. Я помню контекст нашей беседы и умею искать информацию в интернете.")

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
        await message.reply(f"Ошибка: {e}")

async def main():
    print("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
