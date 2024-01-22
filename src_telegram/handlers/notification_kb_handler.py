from aiogram import types, Dispatcher
from magic_filter import F

from schedule.utils import write_user_action
from src_telegram.create import user_db, bot
from src_telegram.handlers.main_kb_handler import pressed_notifications
from src_telegram.keyboards import notification_kb
from src_telegram.handlers.schedule_kb_handler import pressed_back_to_main
from src_telegram.scripts.message_editor import delete_notes


async def pressed_current_week_change(callback: types.CallbackQuery):
    """Обработчик кнопки уведомлений об изменениях на текущую неделю"""
    if user_db.get_user_notification(callback.message.chat.id)[0]:
        write_user_action(callback=callback, action="Выключил уведомление №1")
        user_db.update_is_note_current_week_changes(callback.message.chat.id, False)
    else:
        user_db.update_is_note_current_week_changes(callback.message.chat.id, True)
        write_user_action(callback=callback, action="Включил уведомление №1")

    await pressed_notifications(callback)


async def pressed_sch_next_week(callback: types.CallbackQuery):
    """Обработчик кнопки уведомлений на появления расписания на следующую неделю"""
    if user_db.get_user_notification(callback.message.chat.id)[1]:
        write_user_action(callback=callback, action="Выключил уведомление №2")
        user_db.update_is_note_new_schedule(callback.message.chat.id, False)
    else:
        user_db.update_is_note_new_schedule(callback.message.chat.id, True)
        write_user_action(callback=callback, action="Включил уведомление №2")

    await pressed_notifications(callback)


async def pressed_back(callback: types.CallbackQuery):
    """Обработчик кнопки назад на клавиатуре с уведомлениями"""
    await pressed_back_to_main(callback)


def register_callbacks_schedule_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_back,
                               notification_kb.NotificationsFab.filter(F.action == "pressed_back"))
    dp.callback_query.register(pressed_current_week_change,
                               notification_kb.NotificationsFab.filter(F.action == "pressed_current_week_change"))
    dp.callback_query.register(pressed_sch_next_week,
                               notification_kb.NotificationsFab.filter(F.action == "pressed_sch_next_week"))
