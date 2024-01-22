from aiogram import types, Dispatcher
from aiogram.filters import Command
from src_telegram.create import bot, user_db, sch
from src_telegram.scripts.message_editor import (delete_last_message_from_db,
                                                 delete_current_message_from_user,
                                                 modify_message, delete_notes)
from schedule.utils import add_sign_group_or_teacher, find_coincidence_group_teacher
from src_telegram.keyboards import selection_kb, main_kb
from schedule.utils import is_teacher, add_dash_in_group, write_user_action, check_key
from src_telegram import config


async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    # Если пользователь отправил команду /start не в первый раз и он существует в БД, то удаляем его сообщение

    if user_db.is_user_exists(message.chat.id) is not None:
        await delete_last_message_from_db(message.bot, message.chat.id, user_db.get_cursor())

    message_from_bot = await message.answer(text=f"Привет, {message.from_user.first_name}! 👋 \n"
                                                 f"Введите название группы / ФИО преподавателя.")

    # Удаляем отправленную команду /start у пользователя
    await delete_current_message_from_user(message)

    # Обновляем id последнего сообщения у пользователя
    user_db.update_user_message_id(message_from_bot)
    write_user_action(message=message, action="Отправил /start")


async def message_handler(message: types.Message):
    """Обработчик всех сообщений"""
    write_user_action(message=message, action=f"Отправил {message.text}")

    # Проверка по ключу на получение журнала действий пользователей
    if config.key == message.text:
        if await check_key(message):
            return

    # Удаляем полученное сообщение у пользователя
    await delete_current_message_from_user(message)

    # Если пользователь отправил не текст
    if message.text is None:
        return

    # Сообщение пользователя
    text = message.text.lower()

    if not is_teacher(message.text):
        text = add_dash_in_group(text)

    # Находим совпадения между сообщением пользователя и группами/преподавателями
    coincidence = find_coincidence_group_teacher(text, sch)

    # Получаем id последнего сообщения у пользователя
    last_message_id = user_db.get_last_message_id(message.chat.id)

    # Если мы нашли только 1 совпадение
    if len(coincidence[0]) == 1 and len(coincidence[1]) == 0 or len(coincidence[0]) == 0 and len(coincidence[1]) == 1:
        # Если список групп не пустой и он полностью совпадает с сообщением пользователя

        if len(coincidence[0]):
            if text == list(coincidence[0].values())[0].lower():
                text = coincidence[0].popitem()[1]
                user_db.update_user_current_selection(message.chat.id, text)

                text = add_sign_group_or_teacher(text)

                try:
                    await modify_message(bot, message.chat.id, last_message_id, text=text,
                                         reply_markup=main_kb.get_keyboard(message.chat.id))
                except RuntimeError:
                    message_from_bot = await message.answer(text=text,
                                                            reply_markup=main_kb.get_keyboard(message.chat.id))
                    user_db.update_user_message_id(message_from_bot)

                return
        else:
            if text == list(coincidence[1].values())[0].lower():
                text = coincidence[1].popitem()[1]
                user_db.update_user_current_selection(message.chat.id, text)

                text = add_sign_group_or_teacher(text)

                try:
                    await modify_message(bot, message.chat.id, last_message_id, text=text,
                                         reply_markup=main_kb.get_keyboard(message.chat.id))
                except RuntimeError:
                    message_from_bot = await message.answer(text=text,
                                                            reply_markup=main_kb.get_keyboard(message.chat.id))
                    user_db.update_user_message_id(message_from_bot)

                return

    # Если совпадения не пустые
    if coincidence[0] or coincidence[1]:
        # Пытаемся отредактировать прошлое сообщение
        try:
            await modify_message(bot, message.chat.id, last_message_id, "Возможно вы искали:",
                                 reply_markup=selection_kb.get_selection_kb(coincidence))
        except RuntimeError:
            # Если не получилось отредактировать - отправляем новое и записываем его в БД
            message_from_bot = await message.answer("Были найдены следующие совпадения:",
                                                    reply_markup=selection_kb.get_selection_kb(coincidence))
            user_db.update_user_message_id(message_from_bot)
    else:
        text_message = ("Ничего не найдено 😕\n"
                        "Попробуйте ввести название группы / ФИО преподавателя ещё раз.")

        try:
            await modify_message(bot, message.chat.id, last_message_id, text_message)
        except RuntimeError:
            message_from_bot = await message.answer(text_message)
            user_db.update_user_message_id(message_from_bot)


def register_handlers_message(dp: Dispatcher):
    """Регистрирует обработчики на команду /start и сообщения от пользователя"""
    dp.message.register(start_handler, Command("start"))
    dp.message.register(message_handler)


# TO DO: Это будет классной заготовкой, чтобы удалённо получать данные о пользователях и их все действия удалённо
# @dp.message(Command(""))
# async def handle_get_users_data(message: types.Message):
#    """Обработчик на секретную команду"""
#    pass
