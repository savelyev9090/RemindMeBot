from aiogram.fsm.state import StatesGroup, State

class UserStates(StatesGroup):
    start = State()
    main_menu = State()
    registration = State()

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
    make_a_reminder = State()

class Reminder(StatesGroup):
    make_a_reminder = State()
    enter_time = State()
    enter_date = State()
    enter_title = State()
    enter_description = State()
    edit_reminder = State()
    edit_time = State()
    edit_date = State()
    edit_title = State()
    edit_description = State()