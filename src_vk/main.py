import asyncio
from asyncio import run
from threading import Thread

from vkbottle import Bot
from config import bot_token
from handlers import labelers
from src_vk.main_second_thread import timecheck

bot = Bot(bot_token)

for labeler in labelers:
    bot.labeler.load(labeler)


async def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    my_thread = Thread(target=lambda: loop.run_until_complete(timecheck()))
    my_thread.start()

    await bot.run_polling()


if __name__ == "__main__":
    run(main())
