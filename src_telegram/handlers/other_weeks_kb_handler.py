import re

from aiogram import types, Dispatcher
from magic_filter import F
from src_telegram.scripts.message_editor import modify_message
from src_telegram.handlers.schedule_kb_handler import pressed_back_to_main
from src_telegram.create import bot, user_db, sch
from src_telegram.keyboards import schedule_kb, other_weeks_kb


async def pressed_back(callback: types.CallbackQuery):
    """Обработчик кнопки назад в клавиатуре с другими неделями"""
    await pressed_back_to_main(callback)


async def pressed_week(callback: types.CallbackQuery):
    """Обработчик кнопок выбора других недель"""
    current_selection = user_db.get_user_current_selection(callback.message.chat.id)
    current_week = 0

    # Определяем на какую кнопку нажал пользователь
    for dic in callback.message.reply_markup.inline_keyboard:
        for item in dic:
            if item.callback_data == callback.data:
                # Регулярное выражение \d+$, которое соответствует одному или более цифрам в конце строки
                current_week = int(re.search(r'\d+$', callback.data).group())
                break

    # Определяем группу или преподавателя
    if current_selection.endswith("."):
        current_schedule = sch.get_week_schedule_teacher(current_selection, current_week)
    else:
        current_schedule = sch.get_week_schedule_group(current_selection, current_week)

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text=current_schedule,
                             reply_markup=schedule_kb.get_keyboard(), parse_mode="Markdown")
    except RuntimeError:
        message_from_bot = await callback.message.answer(text=current_schedule, reply_markup=schedule_kb.get_keyboard(),
                                                         parse_mode="Markdown")
        user_db.update_user_message_id(message_from_bot)


def register_callbacks_other_weeks_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_back, other_weeks_kb.OtherWeeksFab.filter(F.action == "pressed_back"))
    dp.callback_query.register(pressed_week, other_weeks_kb.OtherWeeksFab.filter(F.action == "pressed_week"))
