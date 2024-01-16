from aiogram import types, Dispatcher
from magic_filter import F
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class NotificationsFab(CallbackData, prefix="noteFab"):
    """Фабрика колбэков для клавиатуры уведомлений"""
    action: str


def get_keyboard():
    """Возвращает клавиатуру с группами и ФИО преподавателей"""
    builder = InlineKeyboardBuilder()

    builder.button(text="🔕 Изменения на текущей неделе [выкл]",
                   callback_data=NotificationsFab(action="---"))
    builder.button(text="🔕 Новое расписание [выкл]",
                   callback_data=NotificationsFab(action="---"))
    builder.button(text="🔕 Пары на сегодня [выкл]",
                   callback_data=NotificationsFab(action="---"))
    builder.button(text="↩ Вернуться в меню",
                   callback_data=NotificationsFab(action="pressed_back"))

    # Выравниваем кнопки по 1 в ряд
    builder.adjust(1)

    return builder.as_markup()
