from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from source.messages.templates import BUTTONS

if BUTTONS:
    registration_button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTONS.get("registration_button", "Register"))]
        ],
        resize_keyboard=True
    )

    edit_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTONS.get("edit_name", "Edit Name")),
             KeyboardButton(text=BUTTONS.get("edit_age", "Edit Age"))],
            [KeyboardButton(text=BUTTONS.get("edit_email", "Edit Email")),
             KeyboardButton(text=BUTTONS.get("edit_phone", "Edit Phone"))]
        ],
        resize_keyboard=True
    )

    menu_button = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTONS.get("menu_button", "Menu"))]
        ],
        resize_keyboard=True
    )

    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTONS.get("make_a_reminder", "Menu"))],
            [KeyboardButton(text=BUTTONS.get("list_of_reminders", "List of Reminders"))],
        ],
        resize_keyboard=True
    )

    check_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTONS.get("save_changes", "Save Changes"))],
            [KeyboardButton(text=BUTTONS.get("edit_reminder", "Edit"))]
        ],
        resize_keyboard=True
    )

    edit_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTONS.get("edit_title", "Edit Title")),
             KeyboardButton(text=BUTTONS.get("edit_description", "Edit Description"))],
            [KeyboardButton(text=BUTTONS.get("edit_time", "Edit Time")),
             KeyboardButton(text=BUTTONS.get("edit_date", "Edit Reminder"))],
            [KeyboardButton(text=BUTTONS.get("save_changes", "Save Changes"))]
        ],
        resize_keyboard=True
    )