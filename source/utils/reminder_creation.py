from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from database.config import Settings
from source.keyboards.reply import check_keyboard, main_menu
from source.utils.states import Reminder
from source.messages.templates import MESSAGES, BUTTONS
from database.database import Reminder as DBReminder

router = Router()

# Создаем engine для синхронной работы с базой данных
engine = create_engine(Settings.DATABASE_URL, connect_args={"options": "-c timezone=utc"})
Session = sessionmaker(bind=engine)

# Вспомогательная функция для проверки даты и времени
def is_future_datetime(date: datetime) -> bool:
    return date > datetime.now()

# Функция для получения сессии
def get_session():
    return Session()

# Обработка времени
@router.message(Reminder.enter_time)
async def process_reminder_time(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        reminder_time = datetime.strptime(user_input, "%H:%M").time()
        await state.update_data(reminder_time=reminder_time)
        await state.set_state(Reminder.enter_date)
        await message.answer(MESSAGES["prompt_date"])
    except ValueError:
        await message.answer(MESSAGES["invalid_format_time"])

# Обработка даты
@router.message(Reminder.enter_date)
async def process_reminder_date(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        reminder_date = datetime.strptime(user_input, "%d.%m.%Y").date()
        user_data = await state.get_data()
        reminder_time = user_data["reminder_time"]

        reminder_datetime = datetime.combine(reminder_date, reminder_time)
        if not is_future_datetime(reminder_datetime):
            await message.answer(MESSAGES["past_reminder"])
            return

        await state.update_data(reminder_datetime=reminder_datetime)
        await state.set_state(Reminder.enter_title)
        await message.answer(MESSAGES["prompt_title"])
    except ValueError:
        await message.answer(MESSAGES["invalid_format_date"])

# Обработка названия
@router.message(Reminder.enter_title)
async def process_reminder_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 3:
        await message.answer(MESSAGES["too_short"])
        return

    await state.update_data(title=title)
    await state.set_state(Reminder.enter_description)
    await message.answer(MESSAGES["prompt_description"])

# Обработка описания
@router.message(Reminder.enter_description)
async def process_reminder_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if description.lower() == "нет":
        description = None

    user_data = await state.get_data()
    reminder_datetime = user_data["reminder_datetime"]
    title = user_data["title"]

    user_id = message.from_user.id
    session = get_session()
    try:
        new_reminder = DBReminder(
            user_id=user_id,
            deadline=reminder_datetime,
            title=title,
            description=description
        )
        session.add(new_reminder)
        session.commit()

        await message.answer(
            MESSAGES["reminder_created"].format(
                time=reminder_datetime.strftime("%H:%M %d.%m.%Y"),
                title=title,
                description=description or "Без описания"
            ),
            reply_markup=check_keyboard
        )
    finally:
        session.close()

    await state.clear()

# Подтверждение напоминания
@router.message(F.text == BUTTONS["confirm_reminder"])
async def confirm_reminder(message: Message):
    user_id = message.from_user.id
    session = get_session()
    try:
        result = session.execute(select(DBReminder).filter_by(user_id=user_id))
        reminders = result.scalars().all()

        if reminders:
            for reminder in reminders:
                await message.answer(
                    MESSAGES["reminder_saved"].format(
                        time=reminder.deadline.strftime("%H:%M %d.%m.%Y"),
                        title=reminder.title,
                        description=reminder.description or "Без описания"
                    ),
                    reply_markup=main_menu
                )
        else:
            await message.answer("У вас нет текущего создающегося напоминания.")
    finally:
        session.close()

# Редактирование напоминания
@router.message(F.text == BUTTONS["edit_reminder"])
async def edit_reminder_command(message: Message):
    user_id = message.from_user.id
    session = get_session()
    try:
        result = session.execute(select(DBReminder).filter_by(user_id=user_id))
        reminders = result.scalars().all()

        if not reminders:
            await message.answer("У вас нет напоминаний для редактирования.")
            return

        reminder_texts = [f"{r.id}. {r.title} ({r.deadline.strftime('%d.%m.%Y %H:%M')})" for r in reminders]
        await message.answer("Выберите напоминание для редактирования:\n" + "\n".join(reminder_texts))
    finally:
        session.close()

# Редактирование времени
@router.message(Reminder.edit_time)
async def process_edit_time(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        new_time = datetime.strptime(user_input, "%H:%M").time()
        user_data = await state.get_data()
        reminder_id = user_data["reminder_id"]

        session = get_session()
        try:
            reminder = session.get(DBReminder, reminder_id)
            if not reminder:
                await message.answer("Напоминание не найдено.")
                return

            reminder.deadline = reminder.deadline.replace(hour=new_time.hour, minute=new_time.minute)
            session.commit()

            await message.answer(f"🕒 Время успешно изменено на {new_time.strftime('%H:%M')}.")
        finally:
            session.close()
    except ValueError:
        await message.answer("⛔ Неверный формат. Введите время в формате <b>HH:MM</b>.")

# Редактирование даты
@router.message(Reminder.edit_date)
async def process_edit_date(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        new_date = datetime.strptime(user_input, "%d.%m.%Y").date()
        user_data = await state.get_data()
        reminder_id = user_data["reminder_id"]

        session = get_session()
        try:
            reminder = session.get(DBReminder, reminder_id)
            if not reminder:
                await message.answer("Напоминание не найдено.")
                return

            reminder.deadline = datetime.combine(new_date, reminder.deadline.time())
            session.commit()

            await message.answer(f"📅 Дата успешно изменена на {new_date.strftime('%d.%m.%Y')}.")
        finally:
            session.close()
    except ValueError:
        await message.answer("⛔ Неверный формат. Введите дату в формате <b>DD.MM.YYYY</b>.")

# Обработка изменения названия
@router.message(Reminder.edit_title)
async def process_edit_title(message: Message, state: FSMContext):
    new_title = message.text.strip()
    if len(new_title) < 3:
        await message.answer("Название должно быть не короче 3 символов. Попробуйте снова.")
        return

    user_data = await state.get_data()
    reminder_id = user_data["reminder_id"]

    session = get_session()
    try:
        reminder = session.get(DBReminder, reminder_id)
        if not reminder:
            await message.answer("Напоминание не найдено.")
            return

        reminder.title = new_title
        session.commit()

        await message.answer(f"📌 Название успешно изменено на {new_title}.")
        await message.answer(
            f"Текущее напоминание: \n🕒 Время: {reminder.deadline.strftime('%H:%M')}\n"
            f"📅 Дата: {reminder.deadline.strftime('%d.%m.%Y')}\n"
            f"📌 Название: {new_title}\n"
            f"📝 Описание: {reminder.description or 'Без описания'}"
        )
        await message.answer(MESSAGES["edit_reminder"], reply_markup=main_menu)
    finally:
        session.close()

# Обработка изменения описания
@router.message(Reminder.edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    new_description = message.text.strip()
    if new_description.lower() == "нет":
        new_description = None

    user_data = await state.get_data()
    reminder_id = user_data["reminder_id"]

    session = get_session()
    try:
        reminder = session.get(DBReminder, reminder_id)
        if not reminder:
            await message.answer("Напоминание не найдено.")
            return

        reminder.description = new_description
        session.commit()

        await message.answer(f"📝 Описание успешно изменено на: {new_description or 'Без описания'}.")
        await message.answer(
            f"Текущее напоминание: \n🕒 Время: {reminder.deadline.strftime('%H:%M')}\n"
            f"📅 Дата: {reminder.deadline.strftime('%d.%m.%Y')}\n"
            f"📌 Название: {reminder.title}\n"
            f"📝 Описание: {new_description or 'Без описания'}"
        )
        await message.answer(MESSAGES["edit_reminder"], reply_markup=main_menu)
    finally:
        session.close()