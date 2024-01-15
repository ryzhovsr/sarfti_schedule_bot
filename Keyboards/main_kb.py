from typing import Optional
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class KeyboardMain(CallbackData, prefix="main"):
    """Фабрика колбэков для основной клавиатуры"""
    action: str
    value: Optional[int] = None


def get_keyboard():
    """Возвращает клавиатуру с группами и ФИО преподавателей"""
    builder = InlineKeyboardBuilder()

    # builder.button(text=f"👥 Группа {choice}", callback_data=KeyboardMain(action="---"))\
    builder.button(text="🔼 Расписание на текущую неделю", callback_data=KeyboardMain(action="---"))
    builder.button(text="📅 Расписание на другие недели", callback_data=KeyboardMain(action="---"))
    builder.button(text="🔕 Уведомления об изменениях [выкл]", callback_data=KeyboardMain(action="---"))
    builder.button(text="↩ Назад", callback_data=KeyboardMain(action="go_to_back"))

    # Выравниваем кнопки по 1 в ряд
    builder.adjust(1)

    return builder.as_markup()
