from aiogram import types, Dispatcher
from magic_filter import F

from user_actions import write_user_action
from create import bot, user_db, sch
from message_editor import modify_message

import schedule_kb
import main_kb
import notification_kb
import other_weeks_kb

from selection_kb_handler import pressed_back


async def pressed_current_week_sch(callback: types.CallbackQuery):
    """Обработчик кнопки расписания на текущую неделю"""
    # Записываем действие от пользователя
    write_user_action(callback=callback, action="Нажал кнопку 'Расписание на текущую неделю'")
    current_selection = user_db.get_user_current_selection(callback.message.chat.id)

    # Определяем группу или преподавателя
    if current_selection.endswith("."):
        current_schedule = sch.get_week_schedule_teacher(current_selection, sch.get_current_week_id())
    else:
        current_schedule = sch.get_week_schedule_group(current_selection, sch.get_current_week_id())

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    if not current_schedule:
        try:
            await modify_message(bot, callback.message.chat.id, last_message_id, text="Расписание на текущую неделю "
                                                                                      "ещё не готово!",
                                 reply_markup=other_weeks_kb.get_keyboard(current_schedule))
        except RuntimeError:
            message_from_bot = await callback.message.answer(text="Расписание на текущую неделю ещё не готово!",
                                                             reply_markup=other_weeks_kb.get_keyboard(current_schedule))
            user_db.update_user_message_id(message_from_bot)
        return

    else:
        try:
            await modify_message(bot, callback.message.chat.id, last_message_id, text=current_schedule,
                                 reply_markup=schedule_kb.get_keyboard(), parse_mode="Markdown")
        except RuntimeError:
            message_from_bot = await callback.message.answer(text=current_schedule, reply_markup=schedule_kb.get_keyboard(),
                                                             parse_mode="Markdown")
            user_db.update_user_message_id(message_from_bot)


async def pressed_other_week_sch(callback: types.CallbackQuery):
    """Обработчик кнопки расписания на другие недели"""
    # current_selection = user_db.get_user_current_selection(callback.message.chat.id)
    write_user_action(callback=callback, action="Нажал кнопку 'Расписание на другие недели'")
    last_message_id = user_db.get_last_message_id(callback.message.chat.id)
    upcoming_weeks = sch.get_upcoming_weeks_list()

    # Если список будущих недель пустой
    if not bool(upcoming_weeks):
        try:
            await modify_message(bot, callback.message.chat.id, last_message_id, text="Расписание на другие "
                                                                                      "недели ещё не готово!",
                                 reply_markup=other_weeks_kb.get_keyboard(upcoming_weeks))
        except RuntimeError:
            message_from_bot = await callback.message.answer(text="Расписание на другие недели ещё не готово!",
                                                             reply_markup=other_weeks_kb.get_keyboard(upcoming_weeks))
            user_db.update_user_message_id(message_from_bot)
        return

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text="Доступны след. недели",
                             reply_markup=other_weeks_kb.get_keyboard(upcoming_weeks))
    except RuntimeError:
        message_from_bot = await callback.message.answer(text="Доступны след. недели",
                                                         reply_markup=other_weeks_kb.get_keyboard(upcoming_weeks))
        user_db.update_user_message_id(message_from_bot)


async def pressed_notifications(callback: types.CallbackQuery):
    """Обработчик кнопки уведомлений"""
    user_id = callback.message.chat.id
    last_message_id = user_db.get_last_message_id(user_id)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text="Выберете уведомления",
                             reply_markup=notification_kb.get_keyboard(user_id))
    except RuntimeError:
        message_from_bot = await callback.message.answer(text="Выберете уведомления",
                                                         reply_markup=notification_kb.get_keyboard(user_id))
        user_db.update_user_message_id(message_from_bot)


async def pressed_back_main(callback: types.CallbackQuery):
    """Обработчик кнопки назад в main клавиатуре"""
    # Вызываем уже написанный колбэк из другой клавиатуры
    await pressed_back(callback)


def register_callbacks_main_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_current_week_sch, main_kb.MainFab.filter(F.action == "pressed_current_week_sch"))
    dp.callback_query.register(pressed_other_week_sch, main_kb.MainFab.filter(F.action == "pressed_other_week_sch"))
    dp.callback_query.register(pressed_notifications, main_kb.MainFab.filter(F.action == "pressed_notifications"))
    dp.callback_query.register(pressed_back_main, main_kb.MainFab.filter(F.action == "pressed_back"))
