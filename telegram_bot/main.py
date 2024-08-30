"""
Модуль запускает основные процессы для работы телеграм бота.
Регистрирует обработчики на хендлеры
"""

import asyncio

# Модули с хендлерами
import message_handler
import selection_kb_handler
import main_kb_handler
import schedule_kb_handler
import notification_kb_handler
import other_weeks_kb_handler

from asyncio import run
from aiogram import F, types
from create import dp, bot, user_db
from logging import basicConfig, INFO
from threading import Thread
from main_second_thread import timecheck
from message_editor import delete_notes


# Регистрируем обработчики на хендлеры
message_handler.register_handlers_message(dp)
selection_kb_handler.register_callbacks_selection_kb(dp)
main_kb_handler.register_callbacks_main_kb(dp)
schedule_kb_handler.register_callbacks_schedule_kb(dp)
notification_kb_handler.register_callbacks_schedule_kb(dp)
other_weeks_kb_handler.register_callbacks_other_weeks_kb(dp)


@dp.callback_query(F.data == "delete_note")
async def send_random_value(callback: types.CallbackQuery):
    await delete_notes(bot=bot, user_db=user_db, chat_id=callback.message.chat.id)


async def main():
    # Для логов взаимодействия с ботом в консоль
    basicConfig(level=INFO)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    my_thread = Thread(target=lambda: loop.run_until_complete(timecheck()))
    my_thread.start()

    # Запускаем ожидание бота на получение сообщений
    await dp.start_polling(bot)


if __name__ == "__main__":
    run(main())
