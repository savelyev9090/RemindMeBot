from aiogram.fsm.state import StatesGroup, State

class UserState(StatesGroup):
    registration = State()
    start = State()
    main_menu = State()

class RegState(StatesGroup):
    name = State()
    age = State()
    email = State()
    phone = State()
    edit = State()
    confirm = State()
    edit_name = State()
    edit_age = State()
    edit_email = State()
    edit_phone = State()