from aiogram import types, Dispatcher
from magic_filter import F

from src_telegram.keyboards import other_weeks_kb
from src_telegram.handlers.schedule_kb_handler import pressed_back_to_main


async def pressed_back(callback: types.CallbackQuery):
    """Обработчик кнопки назад в клавиатуре с другими неделями"""
    await pressed_back_to_main(callback)


def register_callbacks_other_weeks_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_back, other_weeks_kb.OtherWeeksFab.filter(F.action == "pressed_back"))
