import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from aiogram import Bot
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from Database.config import Settings
from Database.database import Reminder, User
import smtplib

DATABASE_URL = Settings.DATABASE_URL
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)


def calculate_next_interval(deadline, now):
    time_left = deadline - now
    if time_left > timedelta(days=7):
        return timedelta(days=3)
    elif time_left > timedelta(days=1):
        return timedelta(hours=24)
    elif time_left > timedelta(hours=4):
        return timedelta(minutes=1)
    else:
        return timedelta(minutes=1)


async def send_reminder(bot: Bot, user_id: int, message: str):
    try:
        if user_id is None:
            print(f"Ошибка: user_id не может быть None для пользователя")
            return

        await bot.send_message(user_id, message)
        print(f"Напоминание отправлено пользователю {user_id}: {message}")

        user = get_user_by_id(user_id)
        if user and user.email:
            await send_reminder_email(message, user.email)

    except Exception as e:
        print(f"Ошибка при отправке напоминания для {user_id}: {e}")


async def send_reminder_email(body, receiver_email):
    sender_email = Settings.SENDER_EMAIL
    sender_password = Settings.SENDER_PASSWORD

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'НАПОМИНАНИЕ!'

    message.attach(MIMEText(body, 'plain'))

    smtp_server = "smtp.mail.ru"
    smtp_port = 465

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print(f"Сообщение отправлено на email: {receiver_email}")
    except Exception as e:
        print(f"Ошибка при отправке email: {e}")


def get_user_by_id(user_id):
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        return user
    except Exception as e:
        print(f"Ошибка при получении пользователя с user_id {user_id}: {e}")
    finally:
        session.close()


async def check_and_send_reminders(bot: Bot):
    while True:
        now = datetime.now()

        session = Session()
        try:
            result = session.execute(select(Reminder).filter(Reminder.deadline > now))
            reminders = result.scalars().all()

            for reminder in reminders:
                last_reminder = reminder.last_reminder
                if last_reminder is None or (now - last_reminder >= calculate_next_interval(reminder.deadline, now)):
                    message = f"Напоминание: {reminder.title}\n{reminder.description}\nСрок выполнения: {reminder.deadline}"
                    await send_reminder(bot, reminder.user_id, message)
                    reminder.last_reminder = now
                    session.commit()

        except Exception as e:
            print(f"Ошибка при проверке напоминаний: {e}")

        finally:
            session.close()

        await asyncio.sleep(60)


def process_new_user(update, session):
    user_id = update.message.from_user.id

    if user_id is None:
        print(f"Ошибка: user_id не может быть None")
        return

    user_data = {
        "user_id": user_id,
        "name": update.message.from_user.full_name,
        "email": '',
        "phone_number": '',
        "age": 0
    }

    new_user = User(
        id=user_data["user_id"],
        name=user_data["name"],
        email=user_data["email"],
        phone_number=user_data["phone_number"],
        age=user_data["age"]
    )

    session.add(new_user)
    session.commit()
    print(f"Пользователь {new_user.name} добавлен в базу данных.")
