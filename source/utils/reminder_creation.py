from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import source.keyboards.reply as rkb
from source.utils.states import Reminder
from source.messages.templates import MESSAGES, BUTTONS

router = Router()

# Вспомогательная функция для проверки даты и времени
def is_future_datetime(date: datetime) -> bool:
    return date > datetime.now()


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

    # Сохранение напоминания
    await state.update_data(reminder={
        "time": reminder_datetime,
        "title": title,
        "description": description,
    })

    await message.answer(
        MESSAGES["reminder_created"].format(
            time=reminder_datetime.strftime("%H:%M %d.%m.%Y"),
            title=title,
            description=description or "Без описания"
        ),
        reply_markup=rkb.check_keyboard
    )
    await state.set_state(None)


# Подтверждение напоминания
@router.message(F.text == BUTTONS["confirm_reminder"])
async def confirm_reminder(message: Message, state: FSMContext):
    user_data = await state.get_data()
    reminder = user_data["reminder"]

    if reminder:
        # Сохранение напоминания в базу данных
        await message.answer(
            MESSAGES["reminder_saved"].format(
                time=reminder["time"].strftime("%H:%M %d.%m.%Y"),
                title=reminder["title"],
                description=reminder["description"] or "Без описания"
        ),
        reply_markup=rkb.main_menu)
    else:
        await message.answer("У вас нет текущего создающегося напоминания.")

    await state.clear()


# Начало редактирования напоминания с кнопками
@router.message(F.text == BUTTONS["edit_reminder"])
async def edit_reminder_command(message: Message, state: FSMContext):
    user_data = await state.get_data()
    reminder = user_data.get("reminder")
    if not reminder:
        await message.answer("У вас нет текущего создающегося напоминания.")
        return

    # Переходим в режим редактирования
    await state.set_state(Reminder.edit_reminder)
    await message.answer(
        MESSAGES["edit_reminder"],
        reply_markup=rkb.edit_keyboard
    )


# Редактирование времени
@router.message(F.text == BUTTONS["edit_time"])
async def edit_time(message: Message, state: FSMContext):
    await state.set_state(Reminder.edit_time)
    await message.answer("Введите новое время в формате <b>HH:MM</b>:")


# Редактирование даты
@router.message(F.text == BUTTONS["edit_date"])
async def edit_date(message: Message, state: FSMContext):
    await state.set_state(Reminder.edit_date)
    await message.answer("Введите новую дату в формате <b>DD.MM.YYYY</b>:")


# Редактирование названия
@router.message(F.text == BUTTONS["edit_title"])
async def edit_title(message: Message, state: FSMContext):
    await state.set_state(Reminder.edit_title)
    await message.answer("Введите новое название напоминания:")


# Редактирование описания
@router.message(F.text == BUTTONS["edit_description"])
async def edit_description(message: Message, state: FSMContext):
    await state.set_state(Reminder.edit_description)
    await message.answer("Введите новое описание напоминания:")


# Обработка изменения времени
@router.message(Reminder.edit_time)
async def process_edit_time(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        new_time = datetime.strptime(user_input, "%H:%M").time()
        user_data = await state.get_data()
        reminder = user_data.get("reminder")

        # Обновляем время текущего напоминания
        current_date = reminder["time"].date()
        updated_datetime = datetime.combine(current_date, new_time)
        reminder["time"] = updated_datetime
        await state.update_data(reminder=reminder)

        await message.answer(f"🕒 Время успешно изменено на {new_time.strftime('%H:%M')}.")
        await message.answer(
            f"Текущее напоминание: \n🕒 Время: {updated_datetime.strftime('%H:%M')}\n"
            f"📅 Дата: {updated_datetime.strftime('%d.%m.%Y')}\n"
            f"📌 Название: {reminder['title']}\n"
            f"📝 Описание: {reminder['description'] or 'Без описания'}"
        )
        await message.answer(MESSAGES["edit_reminder"], reply_markup=rkb.edit_keyboard)
    except ValueError:
        await message.answer("⛔ Неверный формат. Введите время в формате <b>HH:MM</b>.")


# Обработка изменения даты
@router.message(Reminder.edit_date)
async def process_edit_date(message: Message, state: FSMContext):
    user_input = message.text.strip()
    try:
        new_date = datetime.strptime(user_input, "%d.%m.%Y").date()
        user_data = await state.get_data()
        reminder = user_data.get("reminder")

        # Обновляем дату текущего напоминания
        reminder["time"] = reminder["time"].replace(year=new_date.year, month=new_date.month, day=new_date.day)
        await state.update_data(reminder=reminder)

        await message.answer(f"📅 Дата успешно изменена на {new_date.strftime('%d.%m.%Y')}.")
        await message.answer(
            f"Текущее напоминание: \n🕒 Время: {reminder['time'].strftime('%H:%M')}\n"
            f"📅 Дата: {new_date.strftime('%d.%m.%Y')}\n"
            f"📌 Название: {reminder['title']}\n"
            f"📝 Описание: {reminder['description'] or 'Без описания'}"
        )
        await message.answer(MESSAGES["edit_reminder"], reply_markup=rkb.edit_keyboard)
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
    reminder = user_data.get("reminder")

    # Обновляем название текущего напоминания
    reminder["title"] = new_title
    await state.update_data(reminder=reminder)

    await message.answer(f"📌 Название успешно изменено на {new_title}.")
    await message.answer(
        f"Текущее напоминание: \n🕒 Время: {reminder['time'].strftime('%H:%M')}\n"
        f"📅 Дата: {reminder['time'].strftime('%d.%m.%Y')}\n"
        f"📌 Название: {new_title}\n"
        f"📝 Описание: {reminder['description'] or 'Без описания'}"
    )
    await message.answer(MESSAGES["edit_reminder"], reply_markup=rkb.edit_keyboard)


# Обработка изменения описания
@router.message(Reminder.edit_description)
async def process_edit_description(message: Message, state: FSMContext):
    new_description = message.text.strip()
    if new_description.lower() == "нет":
        new_description = None

    user_data = await state.get_data()
    reminder = user_data.get("reminder")

    # Обновляем описание текущего напоминания
    reminder["description"] = new_description
    await state.update_data(reminder=reminder)

    await message.answer(f"📝 Описание успешно изменено на: {new_description or 'Без описания'}.")
    await message.answer(
        f"Текущее напоминание: \n🕒 Время: {reminder['time'].strftime('%H:%M')}\n"
        f"📅 Дата: {reminder['time'].strftime('%d.%m.%Y')}\n"
        f"📌 Название: {reminder['title']}\n"
        f"📝 Описание: {new_description or 'Без описания'}"
    )
    await message.answer(MESSAGES["edit_reminder"], reply_markup=rkb.edit_keyboard)