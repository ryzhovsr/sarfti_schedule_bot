from typing import Optional
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class KeyboardSchedule(CallbackData, prefix="sch"):
    """Фабрика колбэков для расписания"""
    action: str
    value: Optional[int] = None


def get_keyboard():
    """---"""
    builder = InlineKeyboardBuilder()

    builder.button(text='❓ Информация', callback_data=KeyboardSchedule(action="pressed_info"))
    builder.button(text='🕘 Пары', callback_data=KeyboardSchedule(action="pressed_time"))
    builder.button(text='↩ Вернуться в меню', callback_data=KeyboardSchedule(action="pressed_go_back"))

    # Выравниваем кнопки по 2 в ряд
    builder.adjust(2)

    return builder.as_markup()
