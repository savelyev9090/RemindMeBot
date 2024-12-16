import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, select
from sqlalchemy.ext.declarative import declarative_base
from aiogram import Bot

# Telegram Bot Token
# BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
# bot = Bot(token=BOT_TOKEN)

# Настройка базы данных
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/mydatabase"  # Замените на ваш URL подключения
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Модель напоминаний
Base = declarative_base()


class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, nullable=False)
    message = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    sent = Column(Integer, default=0)


# Функция отправки сообщения
# async def send_reminder(chat_id, message):
#     try:
#         await bot.send_message(chat_id=chat_id, text=message)
#         print(f"Напоминание отправлено: {chat_id} - {message}")
#     except Exception as e:
#         print(f"Ошибка при отправке напоминания {chat_id}: {e}")

# Функция для вычисления интервала напоминания
def calculate_next_interval(deadline, now):
    time_left = deadline - now
    if time_left > timedelta(days=7):
        return timedelta(days=3)
    elif time_left > timedelta(days=1):
        return timedelta(hours=24)
    elif time_left > timedelta(hours=4):
        return timedelta(hours=4)
    else:
        return timedelta(hours=1)


# Асинхронная функция для отправки напоминания
async def send_reminder(message):
    print(f"Напоминание: {message}") # Тут надо сделать чтобы сообщение отпралялось, это Даня будет делать


# Асинхронная функция для проверки напоминаний
async def smart_reminders():
    session = AsyncSessionLocal()
    now = datetime.now()

    # Получаем все напоминания из базы данных
    reminders = session.query(Reminder).all()

    for reminder in reminders:
        deadline = reminder.deadline
        last_reminder = reminder.last_reminder
        next_interval = calculate_next_interval(deadline, now)

        if last_reminder is None or (now - last_reminder >= next_interval):
            await send_reminder(reminder.message)
            reminder.last_reminder = now
            session.commit()  # Сохраняем изменения в базе данных

    session.close()

# Функция отправки напоминаний в указанное время
async def send_reminders_at_deadline():
    async with AsyncSessionLocal() as session:
        while True:
            now = datetime.now()

            # Получаем все напоминания, которые нужно отправить в будущем и ещё не отправлены
            result = await session.execute(
                select(Reminder).where(Reminder.deadline > now, Reminder.sent == 0)
            )
            reminders = result.scalars().all()

            # Сортируем напоминания по времени отправки
            reminders.sort(key=lambda r: r.deadline)

            for reminder in reminders:
                # Время ожидания до отправки
                wait_time = (reminder.deadline - datetime.now()).total_seconds()

                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                # Отправляем напоминание
                await send_reminder(reminder.chat_id, reminder.message)

                # Обновляем статус напоминания
                reminder.sent = 1
                await session.commit()

            # Уходим в паузу до следующей проверки
            await asyncio.sleep(60)


# Основная функция
async def main():
    # Запускаем задачу для отправки напоминаний
    await send_reminders_at_deadline()


# Запуск программы
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")
