from datetime import datetime, timedelta

reminders = [
    {"deadline": "2024-12-20 18:00", "message": "Сдать проект", "last_reminder": None},
]

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

async def check_reminders():
    now = datetime.now()
    for reminder in reminders:
        deadline = datetime.strptime(reminder["deadline"], "%Y-%m-%d %H:%M")
        last_reminder = reminder["last_reminder"]
        next_interval = calculate_next_interval(deadline, now)

        if last_reminder is None or (now - last_reminder >= next_interval):
            await send_reminder(reminder["message"]) #отправка сообщения
            reminder["last_reminder"] = now
