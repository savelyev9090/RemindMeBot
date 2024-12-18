from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
import source.keyboards.reply as rkb
from source.utils.states import Reminder as ReminderState
from source.messages.templates import MESSAGES, BUTTONS
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from Database.database import Reminder
from Database.config import Settings
import logging

# Логирование ошибок
logger = logging.getLogger(__name__)

router = Router()

# Настройка подключения к базе данных
engine = create_engine(Settings.DATABASE_URL, connect_args={"options": "-c timezone=utc+3"})
Session = sessionmaker(bind=engine)


# Вспомогательная функция для проверки даты и времени
def is_future_datetime(date: datetime) -> bool:
    return date > datetime.now()


def delete_expired_reminders():
    session = Session()
    try:
        now = datetime.now()
        expired_reminders = session.query(Reminder).filter(Reminder.deadline < now).all()

        for reminder in expired_reminders:
            session.delete(reminder)

        session.commit()
        logger.info(f"Удалено устаревших напоминаний: {len(expired_reminders)}")
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при удалении устаревших напоминаний: {e}")
    finally:
        session.close()


# Обновление напоминания в базе
async def update_reminder_in_db(reminder_id, **fields):
    session = Session()
    try:
        reminder = session.query(Reminder).get(reminder_id)
        if reminder:
            for key, value in fields.items():
                setattr(reminder, key, value)
            session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при обновлении напоминания: {e}")
        raise
    finally:
        session.close()


# Вспомогательная функция для форматированного вывода напоминания
async def print_formatted_reminder(message: Message, reminder: Reminder):
    await message.answer(
        f"Текущее напоминание: \n\n"
        f"🕒 Время: {reminder.deadline.strftime('%H:%M')}\n"
        f"📅 Дата: {reminder.deadline.strftime('%d.%m.%Y')}\n"
        f"📌 Название: {reminder.title}\n"
        f"📝 Описание: {reminder.description or MESSAGES['no_description']}"
    )


# Обработка времени
@router.message(ReminderState.enter_time)
async def process_reminder_time(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        reminder_time = datetime.strptime(user_input, "%H:%M").time()
        await state.update_data(reminder_time=reminder_time)
        await state.set_state(ReminderState.enter_date)
        await message.answer(MESSAGES["prompt_date"])
    except ValueError:
        await message.answer(MESSAGES["invalid_format_time"])


# Обработка даты
@router.message(ReminderState.enter_date)
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
        await state.set_state(ReminderState.enter_title)
        await message.answer(MESSAGES["prompt_title"])
    except ValueError:
        await message.answer(MESSAGES["invalid_format_date"])


# Обработка названия
@router.message(ReminderState.enter_title)
async def process_reminder_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 3:
        await message.answer(MESSAGES["too_short"])
        return

    await state.update_data(title=title)
    await state.set_state(ReminderState.enter_description)
    await message.answer(MESSAGES["prompt_description"])


# Обработка описания
@router.message(ReminderState.enter_description)
async def process_reminder_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if description.lower() == MESSAGES["no"]:
        description = None

    user_data = await state.get_data()
    reminder_datetime = user_data["reminder_datetime"]
    title = user_data["title"]

    session = Session()
    try:
        new_reminder = Reminder(
            user_id=message.from_user.id,
            deadline=reminder_datetime,
            title=title,
            description=description
        )
        session.add(new_reminder)
        session.commit()

        await message.answer(
            MESSAGES["reminder_created"].format(
                time=reminder_datetime.strftime("%H:%M"),
                date=reminder_datetime.strftime("%d.%m.%Y"),
                title=title,
                description=description or MESSAGES["no_description"]
            ),
            reply_markup=rkb.check_keyboard
        )
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при создании напоминания: {e}")
        await message.answer(MESSAGES["error_creating_reminder"])
    finally:
        session.close()

    await state.clear()


# Начало редактирования напоминания
@router.message(F.text == BUTTONS["edit_reminder"])
async def edit_reminder_command(message: Message, state: FSMContext):
    session = Session()
    try:
        reminder = session.query(Reminder).filter_by(user_id=message.from_user.id).order_by(
            Reminder.deadline.desc()).first()
        if not reminder:
            await message.answer(MESSAGES["no_reminder"])
            return

        await state.set_state(ReminderState.edit_reminder)
        await state.update_data(reminder_id=reminder.id)
        await message.answer(MESSAGES["edit_reminder"], reply_markup=rkb.edit_keyboard)
    except Exception as e:
        logger.error(f"Ошибка при загрузке напоминания: {e}")
        await message.answer(MESSAGES["error_loading_reminder"])
    finally:
        session.close()


@router.message(F.text == BUTTONS["edit_time"])
async def process_edit_time(message: Message, state: FSMContext):
    await message.answer(MESSAGES["new_time"])
    await state.set_state(Reminder.edit_time)


# Обработка изменения времени
@router.message(ReminderState.edit_time)
async def process_edit_time(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        new_time = datetime.strptime(user_input, "%H:%M").time()
        user_data = await state.get_data()

        session = Session()
        reminder = session.query(Reminder).get(user_data["reminder_id"])
        if reminder:
            updated_datetime = datetime.combine(reminder.deadline.date(), new_time)
            await update_reminder_in_db(reminder.id, deadline=updated_datetime)

            await message.answer(f"🕒 Время успешно изменено на {new_time.strftime('%H:%M')}.")
            await print_formatted_reminder(message, reminder)
            await state.clear()
    except ValueError:
        await message.answer(MESSAGES["invalid_format_time"])


@router.message(F.text == BUTTONS["edit_date"])
async def process_edit_date(message: Message, state: FSMContext):
    await message.answer(MESSAGES["new_date"])
    await state.set_state(Reminder.edit_date)


# Обработка изменения даты
@router.message(ReminderState.edit_date)
async def process_edit_date(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        new_date = datetime.strptime(user_input, "%d.%m.%Y").date()
        user_data = await state.get_data()

        session = Session()
        try:
            reminder_id = user_data["reminder_id"]
            reminder = session.query(Reminder).get(reminder_id)

            if not reminder:
                await message.answer(MESSAGES["reminder_not_found"])
                return

            updated_datetime = datetime.combine(new_date, reminder.deadline.time())
            reminder.deadline = updated_datetime
            session.commit()

            await message.answer(f"📅 Дата успешно изменена на {new_date.strftime('%d.%m.%Y')}.")
            await print_formatted_reminder(message, reminder)
            await message.answer(MESSAGES["new_edit_reminder"], reply_markup=rkb.edit_keyboard)
            await state.clear()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при обновлении даты напоминания: {e}")
            await message.answer(MESSAGES["error_updating_reminder"])
        finally:
            session.close()
    except ValueError:
        await message.answer(MESSAGES["invalid_format_date"])


@router.message(F.text == BUTTONS["edit_title"])
async def process_edit_title(message: Message, state: FSMContext):
    await message.answer(MESSAGES["new_title"])
    await state.set_state(Reminder.edit_title)


# Обработка изменения названия
@router.message(ReminderState.edit_title)
async def process_edit_title(message: Message, state: FSMContext):
    new_title = message.text.strip()
    if len(new_title) < 3:
        await message.answer(MESSAGES["too_short"])
        return

    user_data = await state.get_data()

    session = Session()
    try:
        reminder_id = user_data["reminder_id"]
        reminder = session.query(Reminder).get(reminder_id)

        if not reminder:
            await message.answer(MESSAGES["reminder_not_found"])
            return

        reminder.title = new_title
        session.commit()

        await message.answer(f"📌 Название успешно изменено на: {new_title}.")
        await print_formatted_reminder(message, reminder)
        await message.answer(MESSAGES["new_edit_reminder"], reply_markup=rkb.edit_keyboard)
        await state.clear()
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при обновлении названия напоминания: {e}")
        await message.answer(MESSAGES["error_updating_reminder"])
    finally:
        session.close()


@router.message(F.text == BUTTONS["edit_description"])
async def process_edit_description_command(message: Message, state: FSMContext):
    await message.answer(MESSAGES["new_description"])
    await state.set_state(Reminder.edit_description)


# Обработка изменения описания
@router.message(ReminderState.edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    new_description = message.text.strip()
    if new_description.lower() == MESSAGES["no"]:
        new_description = None

    user_data = await state.get_data()

    session = Session()
    try:
        reminder_id = user_data["reminder_id"]
        reminder = session.query(Reminder).get(reminder_id)

        if not reminder:
            await message.answer(MESSAGES["reminder_not_found"])
            return

        reminder.description = new_description
        session.commit()

        await message.answer(f"📝 Описание успешно изменено на: {new_description or 'Без описания'}.")
        await print_formatted_reminder(message, reminder)
        await message.answer(MESSAGES["new_edit_reminder"], reply_markup=rkb.edit_keyboard)
        await state.clear()
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при обновлении описания напоминания: {e}")
        await message.answer(MESSAGES["error_updating_reminder"])
    finally:
        session.close()


@router.message(F.text == BUTTONS["list_of_reminders"])
async def view_reminders(message: Message):
    delete_expired_reminders()

    session = Session()
    try:
        reminders = session.query(Reminder).filter_by(user_id=message.from_user.id).order_by(Reminder.deadline).all()
        if not reminders:
            await message.answer(MESSAGES["no_reminders"])
            return

        for reminder in reminders:
            await print_formatted_reminder(message, reminder)
    except Exception as e:
        logger.error(f"Ошибка при загрузке напоминаний: {e}")
        await message.answer(MESSAGES["error_loading_reminders"])
    finally:
        session.close()
