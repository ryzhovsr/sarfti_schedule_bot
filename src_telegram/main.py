from asyncio import run
from create import dp, bot, sch
from handlers import (message_handler, selection_kb_handler, main_kb_handler,
                      schedule_kb_handler, notification_kb_handler, other_weeks_kb_handler)
from logging import basicConfig, INFO
from threading import Thread
import time
from datetime import datetime

from src_telegram.scripts.user_db import UserDatabase

# для проверки
import os
from timeit import default_timer

message_handler.register_handlers_message(dp)
selection_kb_handler.register_callbacks_selection_kb(dp)
main_kb_handler.register_callbacks_main_kb(dp)
schedule_kb_handler.register_callbacks_schedule_kb(dp)
notification_kb_handler.register_callbacks_schedule_kb(dp)
other_weeks_kb_handler.register_callbacks_other_weeks_kb(dp)


async def main():
    # Для логов взаимодействия с ботом в консоль
    basicConfig(level=INFO)

    my_thread = Thread(target=timecheck)
    my_thread.start()


    # Запускаем ожидание бота на получение сообщений
    await dp.start_polling(bot)

def timecheck():

    global timing
    user_db = UserDatabase()
    # time.sleep(10)
    timing = time.time()
    while True:
        if time.time() - timing > 10:
            timing = time.time()
            nowtime = datetime.now()

            # для проверки работоспособности удаляет файл 327 и переименовывает 328 в 327
            # Необходимо для искусственного создания изменения в расписании
            directory = os.getcwd()
            old_filepath = os.path.join(directory, 'src_telegram\\data\\schedule_week_328.pkl')

            new_filepath = os.path.join(directory, 'src_telegram\\data\\schedule_week_327.pkl')
            os.remove(new_filepath)
            os.rename(old_filepath, new_filepath)
            # конец

            start_time = default_timer()
            if (nowtime.hour >= 7) and (nowtime.hour <= 21):
                # получение списка кортежей всех current_selection, где включены уведомления
                user_tuple_list = user_db.get_all_note_current_week()

                # преобразование списка кортежей в список
                user_list = []
                for user_tuple in user_tuple_list:
                    user_list.append(user_tuple[0])

                # получение всех списков у кого произошли изменения
                # [0] - изменение на текущей неделе
                # [1] -
                # [2] -
                notifications = sch.get_notification(list(set(user_list)))

                # получение списка кортежей с всеми id пользователей, кому нужно отправить уведомление
                user_notifications = []
                for current_selection in notifications[0]:
                    tmp_list = user_db.get_users_by_current_selection(current_selection)
                    for item in tmp_list:
                        user_notifications.append(item[0])

                print('Время выполнения: ', default_timer() - start_time)
                print(user_notifications)



#


if __name__ == "__main__":
    run(main())
