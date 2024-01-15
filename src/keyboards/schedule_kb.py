from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class ScheduleFab(CallbackData, prefix="schFab"):
    """Фабрика колбэков для расписания"""
    action: str


def get_keyboard():
    """---"""
    builder = InlineKeyboardBuilder()

    builder.button(text="❓Информация", callback_data=ScheduleFab(action="pressed_info"))
    builder.button(text="🕘 Пары", callback_data=ScheduleFab(action="pressed_time"))
    builder.button(text="↩ Вернуться в меню", callback_data=ScheduleFab(action="pressed_back"))

    # Выравниваем кнопки по 2 в ряд
    builder.adjust(2)

    return builder.as_markup()
