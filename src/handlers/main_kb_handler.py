from aiogram import types, Dispatcher
from magic_filter import F

from src.create_bot import bot, user_db, sch
from src.message_editor import modify_message
from src.keyboards import schedule_kb, main_kb
from src.handlers.selection_kb_handler import pressed_back


async def pressed_current_week_sch(callback: types.CallbackQuery):
    """Обработчик кнопки расписания на текущую неделю"""
    current_choice = user_db.get_user_current_choice(callback.message.chat.id)

    current_schedule = ""

    # Определяем группу или преподавателя
    if current_choice.endswith("."):
        pass
    else:
        current_schedule = sch.get_week_schedule_group(current_choice)

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text=current_schedule,
                             reply_markup=schedule_kb.get_keyboard(), parse_mode="Markdown")
    except RuntimeError:
        message_from_bot = await callback.message.answer(text=current_schedule, reply_markup=schedule_kb.get_keyboard(),
                                                         parse_mode="Markdown")
        user_db.update_user_message_id(message_from_bot)


async def pressed_back_main(callback: types.CallbackQuery):
    """Обработчик кнопки назад в main клавиатуре"""
    # Вызываем уже написанный колбэк из другой клавиатуры
    await pressed_back(callback)


def register_callbacks_main_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_current_week_sch, main_kb.MainFab.filter(F.action == "pressed_sch_current_week"))
    dp.callback_query.register(pressed_back_main, main_kb.MainFab.filter(F.action == "pressed_back"))
