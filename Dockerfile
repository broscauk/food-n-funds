# Используем стабильную версию Python
FROM python:3.11-slim

# Устанавливаем рабочую папку
WORKDIR /app

# Копируем список библиотек и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код в контейнер
COPY . .

# Команда для запуска
CMD ["python", "bot.py"]
