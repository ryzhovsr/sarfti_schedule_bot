from asyncio import run
from create import dp, bot, sch
from handlers import (message_handler, selection_kb_handler, main_kb_handler,
                      schedule_kb_handler, notification_kb_handler, other_weeks_kb_handler)
from logging import basicConfig, INFO
from threading import Thread
import time
from telebot import types, TeleBot
import telebot
import asyncio
from src_telegram.scripts.user_db import UserDatabase
import config
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# для проверки
import os


message_handler.register_handlers_message(dp)
selection_kb_handler.register_callbacks_selection_kb(dp)
main_kb_handler.register_callbacks_main_kb(dp)
schedule_kb_handler.register_callbacks_schedule_kb(dp)
notification_kb_handler.register_callbacks_schedule_kb(dp)
other_weeks_kb_handler.register_callbacks_other_weeks_kb(dp)


async def main():
    # Для логов взаимодействия с ботом в консоль
    basicConfig(level=INFO)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    my_thread = Thread(target=lambda: loop.run_until_complete(timecheck()))
    my_thread.start()

    # Запускаем ожидание бота на получение сообщений
    await dp.start_polling(bot)


def send_note(tb, users_id: list, is_one: bool):
    """Обработчик кнопки уведомлений"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Закрыть уведомление", callback_data="pressed_close"))

    if is_one:
        for user_id in users_id:
            tb.send_message(user_id, 'Произошли изменения в расписании \n на текущую неделю!', reply_markup=markup)
    else:
        for user_id in users_id:
            tb.send_message(user_id, 'Появилось расписание\nна другие недели!', reply_markup=markup)


def timecheck():
    db = UserDatabase()
    time_init = time.time()
    tb: TeleBot = telebot.TeleBot(token=config.bot_token)

    while True:
        time.sleep(1)
        if time.time() - time_init > 10:
            time_init = time.time()

            """
            # для проверки работоспособности удаляет файл 327 и переименовывает 328 в 327
            # Необходимо для искусственного создания изменения в расписании
            directory = os.getcwd()
            old_filepath = os.path.join(directory, 'src_telegram\\data\\schedule_week_328.pkl')

            new_filepath = os.path.join(directory, 'src_telegram\\data\\schedule_week_327.pkl')
            os.remove(new_filepath)
            os.rename(old_filepath, new_filepath)
            # конец
            """
            # Список выбранных групп/ФИО у людей, кто включил уведомления
            # Первое уведомление
            user_selection_list_note_one = db.get_all_note_current_week()
            unique_set = set(item for tuple_item in user_selection_list_note_one for item in tuple_item)
            user_selection_list_note_one = list(unique_set)
            # Второе уведомление
            user_selection_list_note_two = db.get_all_note_new_schedule()
            unique_set = set(item for tuple_item in user_selection_list_note_two for item in tuple_item)
            user_selection_list_note_two = list(unique_set)

            notifications = sch.get_notification(user_selection_list_note_one, user_selection_list_note_two)

            # получение списка кортежей с всеми id пользователей, кому нужно отправить первое уведомление
            try:
                user_notification_one = []
                for current_selection in notifications[0]:
                    tmp_list = db.get_users_by_current_selection_changes(current_selection)
                    for item in tmp_list:
                        user_notification_one.append(item[0])
                send_note(tb, user_notification_one, True)
            except TypeError:
                pass

            # второе уведомление
            try:
                user_notification_two = []
                for current_selection in notifications[1]:
                    tmp_list = db.get_users_by_current_selection_adding(current_selection)
                    for item in tmp_list:
                        user_notification_two.append(item[0])
                send_note(tb, user_notification_two, False)
            except TypeError:
                pass


if __name__ == "__main__":
    run(main())
