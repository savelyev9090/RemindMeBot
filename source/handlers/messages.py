from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from source.utils.states import UserStates, Reminder

import source.keyboards.reply as rkb

from source.messages.templates import MESSAGES, BUTTONS

router = Router()

@router.message(F.text == BUTTONS["menu_button"])
async def main_menu_command(message: Message, state: FSMContext):
    await state.set_state(UserStates.main_menu)
    await message.answer(MESSAGES["main_menu"], reply_markup=rkb.main_menu)

@router.message(F.text == BUTTONS["make_a_reminder"])
async def make_a_reminder_command(message: Message, state: FSMContext):
    await state.set_state(Reminder.enter_time)
    await message.answer(MESSAGES["prompt_time"])

