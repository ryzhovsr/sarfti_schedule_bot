import asyncio
import logging
import aiogram

from aiogram import Dispatcher
from magic_filter import F

# Свои модули
import config
import message_editor
import utils

from user_db import *
from schedule_data import ScheduleData
from keyboards import group_and_teacher_kb, main_kb, schedule_kb
from aiogram.filters import Command

dp = Dispatcher()


@dp.message(Command("start"))
async def handle_start(message: types.Message):
    """Обработчик команды /start"""
    # Если пользователь отправил команду /start не в первый раз и он существует в БД, то удаляем его сообщение
    if user_db.is_user_exists(message.chat.id) is not None:
        await message_editor.delete_last_message_from_db(message.bot, message.chat.id, user_db.get_cursor())

    message_from_bot = await message.answer(text=f"Привет, {message.from_user.first_name}! 👋 \n"
                                                 f"Введите название группы / ФИО преподавателя.")

    # Удаляем отправленную команду /start у пользователя
    await message_editor.delete_current_message_from_user(message)

    # Обновляем id последнего сообщения у пользователя
    user_db.update_user_message_id(message_from_bot)


@dp.message()
async def handle_any_message(message: types.Message):
    """Обработчик всех сообщений"""
    # Удаляем полученное сообщение у пользователя
    await message_editor.delete_current_message_from_user(message)

    # Если пользователь отправил не текст
    if message.text is None:
        return

    # Находим совпадения между сообщением пользователя и группами/преподавателями
    coincidence = await utils.find_coincidence_group_teacher(message.text, sch)

    # Получаем id последнего сообщения у пользователя
    last_message_id = user_db.get_last_message_id(message.chat.id)

    # Если мы нашли только 1 совпадение
    if len(coincidence[0]) == 1 or len(coincidence[1]) == 1:
        if len(coincidence[0]):
            text = coincidence[0].popitem()[1]
            user_db.update_user_current_choice(message.chat.id, text)
        else:
            text = coincidence[1].popitem()[1]
            user_db.update_user_current_choice(message.chat.id, text)

        text = utils.define_goup_or_teacher(text)

        try:
            await message_editor.modify_message(bot, message.chat.id, last_message_id, text=text,
                                                reply_markup=main_kb.get_keyboard())
        except RuntimeError:
            # Если не получилось отредактировать - отправляем новое и записываем его в БД
            message_from_bot = await message.answer(text=text, reply_markup=main_kb.get_keyboard())
            user_db.update_user_message_id(message_from_bot)

        return

    # Если совпадения не пустые
    if coincidence[0] or coincidence[1]:
        # Пытаемся отредактировать прошлое сообщение
        try:
            await message_editor.modify_message(bot, message.chat.id, last_message_id,
                                                "Возможно вы искали:",
                                                reply_markup=group_and_teacher_kb.get_keyboard(coincidence))
        except RuntimeError:
            # Если не получилось отредактировать - отправляем новое и записываем его в БД
            message_from_bot = await message.answer("Были найдены следующие совпадения:",
                                                    reply_markup=group_and_teacher_kb.get_keyboard(coincidence))
            user_db.update_user_message_id(message_from_bot)
    else:
        text_message = ("Ничего не найдено 😕\n"
                        "Попробуйте ввести название группы / ФИО преподавателя ещё раз.")

        # Пытаемся отредактировать прошлое сообщение, если будет исключение - отправим новое
        try:
            await message_editor.modify_message(bot, message.chat.id, last_message_id, text_message)
        except RuntimeError:
            # Если не получилось отредактировать - отправляем новое и записываем его в БД
            message_from_bot = await message.answer(text_message)
            user_db.update_user_message_id(message_from_bot)


@dp.callback_query(group_and_teacher_kb.KeyboardGroupsTeachers.filter(F.action == "go_to_back"))
async def click_back_group_and_teacher_kb(callback: types.CallbackQuery):
    """Обработчик кнопки назад в клавиатуре выбора группы/ФИО преподавателя"""
    # Получаем id последнего сообщения у пользователя
    last_message_id = user_db.get_last_message_id(callback.message.chat.id)
    text = f"Введите название группы / ФИО преподавателя."

    try:
        await message_editor.modify_message(bot, callback.message.chat.id, last_message_id, text)
    except RuntimeError:
        message_from_bot = await callback.message.answer(text)
        user_db.update_user_message_id(message_from_bot)


@dp.callback_query(group_and_teacher_kb.KeyboardGroupsTeachers.filter(F.action == "choice"))
async def click_group_or_teacher(callback: types.CallbackQuery):
    """Обработчик кнопок выбора группы/ФИО преподавателя"""
    # Получаем id последнего сообщения у пользователя
    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    # Текст кнопкни, на которую нажал пользователь
    current_choice = ''

    for dic in callback.message.reply_markup.inline_keyboard:
        for item in dic:
            if item.callback_data == callback.data:
                current_choice = item.text
            pass

    user_db.update_user_current_choice(callback.message.chat.id, current_choice)
    text = utils.define_goup_or_teacher(current_choice)

    try:
        await message_editor.modify_message(bot, callback.message.chat.id, last_message_id, text=text,
                                            reply_markup=main_kb.get_keyboard())
    except RuntimeError:
        # Если не получилось отредактировать - отправляем новое и записываем его в БД
        message_from_bot = await callback.message.answer(text=text, reply_markup=main_kb.get_keyboard())
        user_db.update_user_message_id(message_from_bot)


@dp.callback_query(main_kb.KeyboardMain.filter(F.action == "go_to_back"))
async def click_back_main(callback: types.CallbackQuery):
    """Обработчик кнопки назад в main клавиатуре"""
    # Вызываем уже написанный коллбэк из другой клавиатуры
    await click_back_group_and_teacher_kb(callback)


@dp.callback_query(schedule_kb.KeyboardSchedule.filter(F.action == "pressed_go_back"))
async def click_back_sch(callback: types.CallbackQuery):
    """Обработчик кнопки назад в клавиатуре с расписанием"""
    current_choise = user_db.get_user_current_choice(callback.message.chat.id)
    current_choise = utils.define_goup_or_teacher(current_choise)

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await message_editor.modify_message(bot, callback.message.chat.id, last_message_id, text=current_choise,
                                            reply_markup=main_kb.get_keyboard())
    except RuntimeError:
        # Если не получилось отредактировать - отправляем новое и записываем его в БД
        message_from_bot = await callback.message.answer(text=current_choise, reply_markup=main_kb.get_keyboard())
        user_db.update_user_message_id(message_from_bot)


@dp.callback_query(main_kb.KeyboardMain.filter(F.action == "schedule_current_week"))
async def click_sch_current_week(callback: types.CallbackQuery):
    """Обработчик кнопки расписания на текущую неделю"""
    current_choise = user_db.get_user_current_choice(callback.message.chat.id)

    current_schedule = ""

    # Определяем группу или преподавателя
    if current_choise.endswith("."):
        pass
    else:
        current_schedule = sch.get_week_schedule_group(current_choise)

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await message_editor.modify_message(bot, callback.message.chat.id, last_message_id, text=current_schedule,
                                            reply_markup=schedule_kb.get_keyboard())
    except RuntimeError:
        # Если не получилось отредактировать - отправляем новое и записываем его в БД
        message_from_bot = await callback.message.answer(text=current_schedule, reply_markup=schedule_kb.get_keyboard())
        user_db.update_user_message_id(message_from_bot)


async def main():
    # Для логов взаимодействия с ботом в консоль
    logging.basicConfig(level=logging.INFO)

    # Запускаем ожидание бота на получение сообщений
    await dp.start_polling(bot)


if __name__ == "__main__":
    user_db = UserDatabase()
    import time
    start = time.time()
    sch = ScheduleData()
    end = time.time()
    print("The time of execution of above program is :",
          (end - start) * 10 ** 3, "ms")
    bot = aiogram.Bot(token=config.bot_token)
    asyncio.run(main())


# TO DO: Это будет классной заготовкой, чтобы удалённо получать данные о пользователях и их все действия удалённо
# @dp.message(Command(""))
# async def handle_get_users_data(message: types.Message):
#    """Обработчик на секретную команду от админов"""
#    pass
