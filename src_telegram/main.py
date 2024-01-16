from asyncio import run
from create import dp, bot
from handlers import (message_handler, selection_kb_handler, main_kb_handler,
                      schedule_kb_handler, notification_kb_handler)
from logging import basicConfig, INFO


message_handler.register_handlers_message(dp)
selection_kb_handler.register_callbacks_selection_kb(dp)
main_kb_handler.register_callbacks_main_kb(dp)
schedule_kb_handler.register_callbacks_schedule_kb(dp)
notification_kb_handler.register_callbacks_schedule_kb(dp)


async def main():
    # Для логов взаимодействия с ботом в консоль
    basicConfig(level=INFO)

    # Запускаем ожидание бота на получение сообщений
    await dp.start_polling(bot)


if __name__ == "__main__":
    run(main())
