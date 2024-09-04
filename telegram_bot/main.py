"""
Модуль запускает основные процессы для работы телеграм бота.
Регистрирует обработчики на хендлеры
"""

from asyncio import run
from aiogram import F, types
from create import dp, bot, user_db
from logging import basicConfig, INFO
from threading import Thread
from main_second_thread import timecheck
from message_editor import delete_notes
from asyncio import new_event_loop, set_event_loop

# Импортируем функции для регистрации хендлеров и колбэков
from main_menu_handlers import register_callbacks_main_menu
from message_handler import register_message_handlers
from selection_kb_handler import register_selection_callbacks
from schedule_kb_handler import register_callbacks_schedule_kb
from other_weeks_kb_handler import register_callbacks_other_weeks_kb
from notification_kb_handler import register_notification_callbacks


# Регистрируем обработчики на хендлеры
register_callbacks_main_menu(dp)
register_message_handlers(dp)
register_selection_callbacks(dp)
register_callbacks_schedule_kb(dp)
register_callbacks_other_weeks_kb(dp)
register_notification_callbacks(dp)


@dp.callback_query(F.data == "delete_note")
async def send_random_value(callback: types.CallbackQuery):
    await delete_notes(bot=bot, user_db=user_db, chat_id=callback.message.chat.id)


async def main():
    # Для логов взаимодействия с ботом в консоль
    basicConfig(level=INFO)

    loop = new_event_loop()
    set_event_loop(loop)
    my_thread = Thread(target=lambda: loop.run_until_complete(timecheck()))
    my_thread.start()

    # Запускаем ожидание бота на получение сообщений
    await dp.start_polling(bot)


if __name__ == "__main__":
    run(main())
