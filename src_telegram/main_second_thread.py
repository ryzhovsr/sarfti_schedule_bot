import time
import telebot

from telebot import TeleBot
from common_modules.utils import restore_user_action
from src_telegram.create import sch
from src_telegram import config
from src_telegram.scripts.user_db import UserDatabase
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def send_note(tb, repeated_user_ids: list, user_ids_first_notification: list, user_ids_second_notification: list,
              db: UserDatabase):
    """Обработчик кнопки уведомлений"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Закрыть уведомление", callback_data="delete_note"))

    # Отправка пользователям оба уведомления
    for user_id in repeated_user_ids:
        note_id = tb.send_message(chat_id=user_id, text='Произошли изменения в\n'
                                                        'расписании на текущей неделе!',
                                  reply_markup=markup).message_id
        db.update_id_note_current_week(note_id=note_id, user_id=user_id)

        note_id = tb.send_message(chat_id=user_id, text='Появилось расписание\n'
                                                        'на новую неделю!',
                                  reply_markup=markup).message_id
        db.update_id_note_new_schedule(note_id=note_id, user_id=user_id)

    # Отправляем пользователям первое уведомление
    for user_id in user_ids_first_notification:
        note_id = tb.send_message(chat_id=user_id, text='Произошли изменения в\n'
                                                        'расписании на текущей неделе!',
                                  reply_markup=markup).message_id
        db.update_id_note_current_week(note_id=note_id, user_id=user_id)

    # Отправляем пользователям второе уведомление
    for user_id in user_ids_second_notification:
        note_id = tb.send_message(chat_id=user_id, text='Появилось расписание\n'
                                                        'на новую неделю!',
                                  reply_markup=markup).message_id
        db.update_id_note_new_schedule(note_id=note_id, user_id=user_id)


def timecheck():
    db = UserDatabase()
    time_init = time.time()
    tb: TeleBot = telebot.TeleBot(token=config.bot_token_tg)
    time_restore_user_actions = time.time()

    while True:

        time.sleep(3)

        if time.time() - time_init > 5:
            time_init = time.time()

            # Удаляем журнал действий пользователей 1 раз в неделю
            if time_init - time_restore_user_actions > 604800:
                print(1)
                time_restore_user_actions = time_init
                restore_user_action()

            # для проверки работоспособности удаляет файл 327 и переименовывает 328 в 327
            # Необходимо для искусственного создания изменения в расписании
            # directory = os.getcwd()
            # old_filepath = os.path.join(directory, 'src_telegram\\data\\schedule_week_329.pkl')
            #
            # new_filepath = os.path.join(directory, 'src_telegram\\data\\schedule_week_328.pkl')
            # os.remove(new_filepath)
            # os.rename(old_filepath, new_filepath)
            # конец

            # Список выбранных групп/ФИО у людей, кто включил уведомления
            # Первое уведомление
            user_selection_list_note_one = db.get_all_note_current_week()
            unique_set = set(item for tuple_item in user_selection_list_note_one for item in tuple_item)
            user_selection_list_note_one = list(unique_set)

            notifications = sch.get_notification(user_selection_list_note_one)

            # получение списка кортежей с всеми id пользователей, кому нужно отправить первое уведомление
            user_notification_one = []
            user_notification_two = []
            try:
                for current_selection in notifications[0]:
                    tmp_list = db.get_users_by_current_selection_changes(current_selection)
                    for item in tmp_list:
                        user_notification_one.append(item[0])
            except TypeError:
                pass

            if notifications[1]:
                tmp_list = db.get_users_by_current_selection_adding()
                for item in tmp_list:
                    user_notification_two.append(item[0])

            if user_notification_one != [] and user_notification_two != []:
                unique_user_notification_one = [x for x in user_notification_one if x not in user_notification_two]
                unique_user_notification_two = [x for x in user_notification_two if x not in user_notification_one]
                repeated_user_notification = list(set(user_notification_one) & set(user_notification_two))
                send_note(tb, repeated_user_notification, unique_user_notification_one, unique_user_notification_two,
                          db=db)
            else:
                send_note(tb, [], user_notification_one, user_notification_two, db=db)
