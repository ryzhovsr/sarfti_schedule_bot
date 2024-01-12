import asyncio
import logging
import aiogram

from aiogram import Dispatcher
from aiogram.filters import Command

# Свои модули
import config
import edit_message
import callback_factory

from userdb import *
from utils import find_coincidence_group_teacher
from schedule_data import ScheduleData

dp = Dispatcher()


@dp.message(Command("start"))
async def handle_start(message: types.Message):
    """Обработчик команды /start"""
    # Если пользователь отправил команду /start не в первый раз и он существует в БД, то удаляем его сообщение
    if user_db.is_user_exists(message.chat.id) is not None:
        await edit_message.delete_last_message_from_db(message.bot, message.chat.id, user_db.get_cursor())

    message_from_bot = await message.answer(text=f"Привет, {message.from_user.first_name}! 👋 \n"
                                                 f"Введите название группы / ФИО преподавателя.")

    # Удаляем отправленную команду /start у пользователя
    await edit_message.delete_current_message_from_user(message)

    # Обновляем id последнего сообщения у пользователя
    user_db.update_user_message_id(message_from_bot)


@dp.message()
async def handle_any_message(message: types.Message):
    """Обработчик всех сообщений"""

    # Удаляем полученное сообщение у пользователя
    await edit_message.delete_current_message_from_user(message)

    # Находим совпадения между сообщением пользователя и группами/преподавателями
    coincidence = await find_coincidence_group_teacher(message.text, sch)

    # Получаем id последнего сообщения у пользователя
    last_message_id = user_db.get_last_message_id(message.chat.id)

    # Если совпадения не пустые
    if coincidence[0] or coincidence[1]:
        # Пытаемся отредактировать прошлое сообщение, если будет исключение - отправим новое
        try:
            message_from_bot = await edit_message.modify_message(bot, message.chat.id, last_message_id,
                                                                 "Были найдены следующие совпадения:",
                                                                 reply_markup=callback_factory.
                                                                 get_groups_teachers_fab(coincidence))
        except RuntimeError:
            message_from_bot = await message.answer("Были найдены следующие совпадения:",
                                                    reply_markup=callback_factory.get_groups_teachers_fab(coincidence))
    else:
        text_message = ("Ничего не найдено 😕\n"
                        "Попробуйте ввести название группы / ФИО преподавателя ещё раз.")

        # Пытаемся отредактировать прошлое сообщение, если будет исключение - отправим новое
        try:
            message_from_bot = await edit_message.modify_message(bot, message.chat.id, last_message_id, text_message)
        except RuntimeError:
            message_from_bot = await message.answer(text_message)

    user_db.update_user_message_id(message_from_bot)


async def main():
    # Для логов взаимодействия с ботом в консоль
    logging.basicConfig(level=logging.INFO)

    # Запускаем ожидание бота на получение сообщений
    await dp.start_polling(bot)


if __name__ == "__main__":
    user_db = UserDatabase()
    sch = ScheduleData()
    bot = aiogram.Bot(token=config.bot_token)
    asyncio.run(main())


# TO DO: Это будет классной заготовкой, чтобы удалённо получать данные о пользователях и их все действия удалённо
# @dp.message(Command(""))
# async def handle_get_users_data(message: types.Message):
#    """Обработчик на секретную команду от админов"""
#    pass
