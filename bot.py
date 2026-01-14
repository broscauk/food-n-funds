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

# Переключаемся на максимально стабильную модель 1.0 Pro
# Она поддерживает текстовое общение и лучше всего работает в старых регионах API
model = genai.GenerativeModel(
    model_name="gemini-1.0-pro",
    system_instruction=SYSTEM_PROMPT
)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
chat_sessions = {}

def get_chat(user_id):
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])
    return chat_sessions[user_id]

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    chat_sessions[user_id] = model.start_chat(history=[])
    await message.answer("Бот запущен на стабильной модели Gemini 1.0 Pro. Я готов к общению!")

@dp.message(F.text)
async def text_handler(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    chat = get_chat(message.from_user.id)
    try:
        response = chat.send_message(message.text)
        if response.text:
            await message.reply(response.text)
        else:
            await message.reply("К сожалению, я не смог сформулировать ответ. Попробуй другой вопрос.")
    except Exception as e:
        await message.reply(f"Ошибка системы: {str(e)}")

# В модели 1.0 Pro работа с аудио отличается, поэтому пока сфокусируемся на тексте
@dp.message(F.voice)
async def voice_stub(message: types.Message):
    await message.reply("В текущем стабильном режиме я временно принимаю только текстовые сообщения.")

async def main():
    print("Бот запускается на модели 1.0 Pro...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
