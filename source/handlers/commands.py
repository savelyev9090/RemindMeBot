from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import source.keyboards.reply as rkb

from source.utils.states import UserStates
from source.messages.templates import MESSAGES

router = Router()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.set_state(UserStates.start)
    await message.answer(MESSAGES["start_message"], reply_markup=rkb.registration_button)

@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext):
    await state.set_state(UserStates.main_menu)
    await message.answer(MESSAGES["main_menu"], reply_markup=rkb.main_menu)
