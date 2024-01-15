from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MainFab(CallbackData, prefix="mainFab"):
    """Фабрика колбэков для основной клавиатуры"""
    action: str


def get_keyboard():
    """Возвращает клавиатуру с группами и ФИО преподавателей"""
    builder = InlineKeyboardBuilder()

    builder.button(text="🔼 Расписание на текущую неделю", callback_data=MainFab(action="pressed_sch_current_week"))
    builder.button(text="📅 Расписание на другие недели", callback_data=MainFab(action="---"))
    builder.button(text="🔕 Уведомления об изменениях [выкл]", callback_data=MainFab(action="---"))
    builder.button(text="↩ Назад", callback_data=MainFab(action="pressed_back"))

    # Выравниваем кнопки по 1 в ряд
    builder.adjust(1)

    return builder.as_markup()
