import os
import time

import vk_api
from vk_api import VkApiError
from vk_api.vk_api import VkApiMethod

from src_vk.config import bot_token
from src_vk.create import sch
from src_vk.keyboards import notification_kb
from src_vk.scripts.user_db import UserDatabase


def send_note(vk: VkApiMethod, repeated_user_ids: list, user_ids_first_notification: list,
              user_ids_second_notification: list,
              db: UserDatabase):
    """Отправляет уведомление пользователям"""
    # Отправка пользователям оба уведомления
    for user_id in repeated_user_ids:
        try:
            vk.messages.delete(peer_id=user_id, message_ids=db.get_last_message_id(user_id), delete_for_all=True)
        except VkApiError:
            vk.messages.edit(peer_id=user_id, message_id=db.get_last_message_id(user_id), message="ㅤ")
        message_from_bot = vk.messages.send(peer_id=user_id, random_id=0,
                                            message="Произошли изменения в\n"
                                                    "расписании на текущей неделе!\n"
                                                    "Появилось расписание\n"
                                                    "на другие недели!",
                                            keyboard=notification_kb.get_close_kb())
        db.update_message_id(user_id, message_from_bot)

    # Отправляем пользователям первое уведомление
    for user_id in user_ids_first_notification:
        try:
            vk.messages.delete(peer_id=user_id, message_ids=db.get_last_message_id(user_id), delete_for_all=True)
        except VkApiError:
            vk.messages.edit(peer_id=user_id, message_id=db.get_last_message_id(user_id), message="ㅤ")
        message_from_bot = vk.messages.send(peer_id=user_id, random_id=0,
                                            message="Произошли изменения в\n"
                                                    "расписании на текущей неделе!",
                                            keyboard=notification_kb.get_close_kb())
        db.update_message_id(user_id, message_from_bot)

    # Отправляем пользователям второе уведомление
    for user_id in user_ids_second_notification:
        try:
            vk.messages.delete(peer_id=user_id, message_ids=db.get_last_message_id(user_id), delete_for_all=True)
        except VkApiError:
            vk.messages.edit(peer_id=user_id, message_id=db.get_last_message_id(user_id), message="ㅤ")
        message_from_bot = vk.messages.send(peer_id=user_id, random_id=0,
                                            message="Появилось расписание\n"
                                                    "на другие недели!",
                                            keyboard=notification_kb.get_close_kb())
        db.update_message_id(user_id, message_from_bot)


def timecheck():
    db = UserDatabase()
    time_init = time.time()
    vk_session = vk_api.VkApi(token=bot_token)
    vk = vk_session.get_api()

    while True:

        time.sleep(3)

        if time.time() - time_init > 5:
            time_init = time.time()

            # для проверки работоспособности удаляет файл 327 и переименовывает 328 в 327
            # Необходимо для искусственного создания изменения в расписании
            # directory = os.getcwd()
            # old_filepath = os.path.join(directory, 'src_vk\\data\\schedule_week_329.pkl')
            #
            # new_filepath = os.path.join(directory, 'src_vk\\data\\schedule_week_328.pkl')
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

                send_note(vk, repeated_user_notification, unique_user_notification_one, unique_user_notification_two,
                          db)
            else:
                send_note(vk, [], user_notification_one, user_notification_two, db)
