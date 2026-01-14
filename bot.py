import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import google.generativeai as genai

# --- ЗАГРУЗКА НАСТРОЕК ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Роль бота
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "Ты — универсальный ИИ-ассистент. Отвечай кратко и по делу.")

# --- НАСТРОЙКА AI ---
# Настраиваем API без явного указания версии, чтобы библиотека выбрала стабильную
genai.configure(api_key=GEMINI_API_KEY)

# Используем максимально простую инициализацию без параметров 'tools'
# Это уберет причину ошибки 404
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
chat_sessions = {}

def get_chat(user_id):
    if user_id not in chat_sessions:
        # Инициализируем чат с памятью контекста
        chat_sessions[user_id] = model.start_chat(history=[])
    return chat_sessions[user_id]

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    chat_sessions[user_id] = model.start_chat(history=[]) # Очистка истории при рестарте
    await message.answer("Бот запущен в стабильном режиме! Чем я могу тебе помочь?")

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
        # Отправляем аудио на обработку
        response = chat.send_message([
            "Прослушай и ответь на это сообщение:", 
            {"mime_type": "audio/ogg", "data": audio_data}
        ])
        await message.reply(response.text)
    except Exception as e:
        await message.reply(f"Ошибка при обработке голоса: {e}")
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
        # Если ошибка все равно возникнет, мы увидим её текст
        await message.reply(f"Произошла ошибка: {str(e)}")

async def main():
    print("Бот успешно запущен в облаке...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
