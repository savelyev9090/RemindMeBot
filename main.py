import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from source.utils.notificator import check_and_send_reminders
from source.handlers import commands
from source.handlers import messages
from source.utils import registration
from source.utils import reminder_creation

bot = Bot(token='7891533502:AAGRhzF1ksBSfH2pku3SQoCUhwHHFtkR6tI', default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def include_all_routers(dp):
    dp.include_router(commands.router)
    dp.include_router(messages.router)
    dp.include_router(registration.router)
    dp.include_router(reminder_creation.router)


async def main():
    try:
        if await bot.get_webhook_info():
            await bot.delete_webhook(drop_pending_updates=True)

        include_all_routers(dp)
        await dp.start_polling(bot)
        await check_and_send_reminders(bot)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    asyncio.run(main())
