import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config_reader import settings

from source.handlers import commands
from source.handlers import messages

from source.utils import registration
from source.utils import reminder_creation

bot = Bot(token=settings.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode="HTML"))
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
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    asyncio.run(main())