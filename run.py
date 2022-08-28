import asyncio


def run():
    loop = asyncio.get_event_loop()

    from olxbot.bot import bot
    from olxbot.db import db
    from olxbot.olx import start_olx_polling
    loop.create_task(start_olx_polling(bot, db, loop))

    from olxbot.db import start_daily_cleaning
    loop.create_task(start_daily_cleaning())

    from olxbot.bot import dp
    from aiogram.utils import executor
    print('Ready!')
    executor.start_polling(dp, loop=loop)


if __name__ == '__main__':
    run()