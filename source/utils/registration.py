import json
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import source.keyboards.reply as rkb
from source.utils.states import UserStates, RegState
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database.database import User
from database.config import Settings

router = Router()

# Логирование ошибок
logger = logging.getLogger(__name__)

engine = create_engine(Settings.DATABASE_URL, connect_args={"options": "-c timezone=utc"})
Session = sessionmaker(bind=engine)

# Путь к файлам
USER_DATA_PATH = "/Users/leonidserbin/Downloads/RemindMe/source/users.json"
MESSAGES_PATH = "/Users/leonidserbin/Downloads/RemindMe/source/messages/ru.json"


# Сохранение данных пользователя в JSON
def save_user_to_json(user_data):
    try:
        with open(USER_DATA_PATH, "r", encoding="utf-8") as file:
            existing_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error reading JSON file: {e}")
        existing_data = []

    existing_data.append(user_data)

    try:
        with open(USER_DATA_PATH, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error writing to JSON file: {e}")
        return False
    return True


# Загрузка сообщений и кнопок
def load_messages_and_buttons(language: str):
    try:
        with open(MESSAGES_PATH.format(language=language), "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading messages for language '{language}': {e}")
        return {}


MESSAGES = load_messages_and_buttons("ru").get("messages", {})
BUTTONS = load_messages_and_buttons("ru").get("buttons", {})


# Проверка валидности данных
def is_valid_age(age: str) -> bool:
    return age.isdigit() and 0 < int(age) < 120


def is_valid_email(email: str) -> bool:
    return "@" in email and "." in email


def is_valid_phone(phone: str) -> bool:
    return phone.isdigit() and len(phone) in [10, 11]


# Создание клавиатуры для подтверждения данных
def create_confirmation_markup():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTONS["confirm"]), KeyboardButton(text=BUTTONS["edit"])]
        ],
        resize_keyboard=True
    )


# Шаги регистрации
@router.message(F.text == BUTTONS["registration_button"])
async def start_registration(message: Message, state: FSMContext):
    await message.answer(MESSAGES["registration_message"])
    await state.set_state(RegState.name)


@router.message(RegState.name)
async def process_name(message: Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer(MESSAGES["name_invalid"])
        return
    await state.update_data(name=message.text.strip())

    user_data = await state.get_data()
    session = Session()

    existing_user = session.query(User).filter_by(id=message.from_user.id).first()
    if existing_user:
        existing_user.name = user_data['name']
    else:
        new_user = User(
            id=message.from_user.id,
            email=user_data.get('email', ''),
            phone_number=user_data.get('phone', ''),
            age=user_data.get('age', 0),
            name=user_data['name']
        )
        session.add(new_user)

    session.commit()
    session.close()

    await state.set_state(RegState.age)
    await message.answer(MESSAGES["age_request"])


@router.message(RegState.age)
async def process_age(message: Message, state: FSMContext):
    user_age = message.text.strip()
    if not is_valid_age(user_age):
        await message.answer(MESSAGES["age_invalid"])
        return
    await state.update_data(age=user_age)

    user_data = await state.get_data()
    session = Session()

    existing_user = session.query(User).filter_by(id=message.from_user.id).first()
    if existing_user:
        existing_user.age = user_data['age']
    else:
        new_user = User(
            id=message.from_user.id,
            email=user_data.get('email', ''),
            phone_number=user_data.get('phone', ''),
            age=user_data['age'],
            name=user_data.get('name', '')
        )
        session.add(new_user)

    session.commit()
    session.close()

    await state.set_state(RegState.email)
    await message.answer(MESSAGES["email_request"])


@router.message(RegState.email)
async def process_email(message: Message, state: FSMContext):
    user_email = message.text.strip()
    if not is_valid_email(user_email):
        await message.answer(MESSAGES["email_invalid"])
        return
    await state.update_data(email=user_email)

    user_data = await state.get_data()
    session = Session()

    existing_user = session.query(User).filter_by(id=message.from_user.id).first()
    if existing_user:
        existing_user.email = user_data['email']
    else:
        new_user = User(
            id=message.from_user.id,
            email=user_data['email'],
            phone_number=user_data.get('phone', ''),
            age=user_data.get('age', 0),
            name=user_data.get('name', '')
        )
        session.add(new_user)

    session.commit()
    session.close()

    await state.set_state(RegState.phone)
    await message.answer(MESSAGES["phone_request"])


@router.message(RegState.phone)
async def process_phone(message: Message, state: FSMContext):
    user_phone = message.text.strip()
    if not is_valid_phone(user_phone):
        await message.answer(MESSAGES["phone_invalid"])
        return
    await state.update_data(phone=user_phone)

    user_data = await state.get_data()
    session = Session()

    existing_user = session.query(User).filter_by(id=message.from_user.id).first()
    if existing_user:
        existing_user.phone_number = user_data['phone']
    else:
        new_user = User(
            id=message.from_user.id,
            email=user_data.get('email', ''),
            phone_number=user_data['phone'],
            age=user_data.get('age', 0),
            name=user_data.get('name', '')
        )
        session.add(new_user)

    session.commit()
    session.close()

    user_data = await state.get_data()
    await message.answer(
        f"{MESSAGES['confirmation']}\n\n"
        f"Имя: {user_data['name']}\n"
        f"Возраст: {user_data['age']}\n"
        f"Email: {user_data['email']}\n"
        f"Телефон: {user_data['phone']}",
        reply_markup=create_confirmation_markup()
    )
    await state.set_state(RegState.confirm)


@router.message(RegState.confirm)
async def confirm_data(message: Message, state: FSMContext):
    user_response = message.text.strip()
    user_data = await state.get_data()

    if user_response == BUTTONS["confirm"]:
        session = Session()
        existing_user = session.query(User).filter_by(id=message.from_user.id).first()

        if not existing_user:
            new_user = User(
                id=message.from_user.id,
                email=user_data['email'],
                phone_number=user_data['phone'],
                age=user_data['age'],
                name=user_data['name']
            )
            session.add(new_user)
            session.commit()

        session.close()

        await message.answer(MESSAGES["registration_complete"], reply_markup=rkb.menu_button)
        await state.clear()
        await state.set_state(UserStates.main_menu)
    elif user_response == BUTTONS["edit"]:
        await message.answer(MESSAGES["edit_prompt"], reply_markup=rkb.edit_menu)
        await state.set_state(RegState.edit)
    else:
        await message.answer(MESSAGES["confirmation_invalid"])


# Обновление данных
@router.message(RegState.edit)
async def edit_data(message: Message, state: FSMContext):
    edit_choice = message.text.strip()

    if edit_choice == BUTTONS["edit_name"]:
        await message.answer(MESSAGES["name_request"])
        await state.set_state(RegState.edit_name)
    elif edit_choice == BUTTONS["edit_age"]:
        await message.answer(MESSAGES["age_request"])
        await state.set_state(RegState.edit_age)
    elif edit_choice == BUTTONS["edit_email"]:
        await message.answer(MESSAGES["email_request"])
        await state.set_state(RegState.edit_email)
    elif edit_choice == BUTTONS["edit_phone"]:
        await message.answer(MESSAGES["phone_request"])
        await state.set_state(RegState.edit_phone)
    else:
        await message.answer(MESSAGES["edit_invalid"])


# Обновление конкретных данных и возврат к подтверждению
async def return_to_confirmation(message: Message, state: FSMContext):
    user_data = await state.get_data()
    await message.answer(
        f"{MESSAGES['confirmation']}\n\n"
        f"Имя: {user_data['name']}\n"
        f"Возраст: {user_data['age']}\n"
        f"Email: {user_data['email']}\n"
        f"Телефон: {user_data['phone']}",
        reply_markup=create_confirmation_markup()
    )
    await state.set_state(RegState.confirm)


# Редактирование данных
@router.message(RegState.edit_name)
async def update_name(message: Message, state: FSMContext):
    if len(message.text.strip()) < 2:
        await message.answer(MESSAGES["name_invalid"])
        return
    await state.update_data(name=message.text.strip())

    user_data = await state.get_data()
    session = Session()

    existing_user = session.query(User).filter_by(id=message.from_user.id).first()
    if existing_user:
        existing_user.name = user_data['name']

    session.commit()
    session.close()

    await return_to_confirmation(message, state)


# Редактирование возраста
@router.message(RegState.edit_age)
async def update_age(message: Message, state: FSMContext):
    user_age = message.text.strip()
    if not is_valid_age(user_age):
        await message.answer(MESSAGES["age_invalid"])
        return
    await state.update_data(age=user_age)

    user_data = await state.get_data()
    session = Session()

    existing_user = session.query(User).filter_by(id=message.from_user.id).first()
    if existing_user:
        existing_user.age = user_data['age']
    else:
        new_user = User(
            id=message.from_user.id,
            email=user_data.get('email', ''),
            phone_number=user_data.get('phone', ''),
            age=user_data['age'],
            name=user_data.get('name', '')
        )
        session.add(new_user)

    session.commit()
    session.close()

    await return_to_confirmation(message, state)


# Редактирование email
@router.message(RegState.edit_email)
async def update_email(message: Message, state: FSMContext):
    user_email = message.text.strip()
    if not is_valid_email(user_email):
        await message.answer(MESSAGES["email_invalid"])
        return
    await state.update_data(email=user_email)

    user_data = await state.get_data()
    session = Session()

    existing_user = session.query(User).filter_by(id=message.from_user.id).first()
    if existing_user:
        existing_user.email = user_data['email']
    else:
        new_user = User(
            id=message.from_user.id,
            email=user_data['email'],
            phone_number=user_data.get('phone', ''),
            age=user_data.get('age', 0),
            name=user_data.get('name', '')
        )
        session.add(new_user)

    session.commit()
    session.close()

    await return_to_confirmation(message, state)


# Редактирование телефона
@router.message(RegState.edit_phone)
async def update_phone(message: Message, state: FSMContext):
    user_phone = message.text.strip()
    if not is_valid_phone(user_phone):
        await message.answer(MESSAGES["phone_invalid"])
        return
    await state.update_data(phone=user_phone)

    user_data = await state.get_data()
    session = Session()

    existing_user = session.query(User).filter_by(id=message.from_user.id).first()
    if existing_user:
        existing_user.phone_number = user_data['phone']
    else:
        new_user = User(
            id=message.from_user.id,
            email=user_data.get('email', ''),
            phone_number=user_data['phone'],
            age=user_data.get('age', 0),
            name=user_data.get('name', '')
        )
        session.add(new_user)

    session.commit()
    session.close()

    await return_to_confirmation(message, state)
