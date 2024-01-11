import asyncio
import logging
import aiogram

from aiogram import Dispatcher
from aiogram.filters import Command

# Свои модули
import config
import edit_message

from database import *

dp = Dispatcher()


@dp.message(Command("start"))
async def handle_start(message: types.Message):
    """Обработчик команды /start"""
    # Если пользователь отправил команду /start не в первый раз и он существует в БД, то удаляем его сообщение
    if db.is_user_exists(message.chat.id) is not None:
        await edit_message.delete_last_message_from_db(message.bot, message.chat.id, db.get_cursor())

    message_from_bot = await message.answer(text=f"Привет, {message.from_user.first_name}! 👋 \n"
                                                 f"Введите название группы / ФИО преподавателя.")

    # Удаляем отправленную команду /start у пользователя
    await edit_message.delete_current_message_from_user(message)

    # Обновляем id последнего сообщения у пользователя
    db.update_user_message_id(message_from_bot)


@dp.message()
async def handle_any_message(message: types.Message):
    """Обработчик всех сообщений"""
    await edit_message.delete_last_message_from_db(message.bot, message.chat.id, db.get_cursor())
    await edit_message.delete_current_message_from_user(message)

    message_from_bot = ""

    if message.text and 0:
        pass
        # TO DO: Здесь будет реализация поиска по заданному сообщению преподавателя или группы
    else:
        message_from_bot = await message.answer(text="Ничего не найдено😕\n"
                                                     "Попробуйте ввести название группы / ФИО преподавателя ещё раз.")

    db.update_user_message_id(message_from_bot)


async def main():
    # Для логов взаимодействия с ботом в консоль
    logging.basicConfig(level=logging.INFO)

    # Запускаем ожидание бота на получение сообщений
    await dp.start_polling(bot)


if __name__ == "__main__":
    db = Database()
    bot = aiogram.Bot(token=config.bot_token)
    asyncio.run(main())


# TO DO: Это будет классной заготовкой, чтобы удалённо получать данные о пользователях и их все действия удалённо
# @dp.message(Command(""))
# async def handle_get_users_data(message: types.Message):
#    """Обработчик на секретную команду от админов"""
#    pass
