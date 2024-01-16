from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src_telegram.create import user_db


class NotificationsFab(CallbackData, prefix="noteFab"):
    """Фабрика колбэков для клавиатуры уведомлений"""
    action: str


def get_keyboard(user_id: int):
    """Возвращает клавиатуру с группами и ФИО преподавателей"""
    builder = InlineKeyboardBuilder()

    notifications = user_db.get_user_notification(user_id)

    if notifications[0]:
        builder.button(text="🔔 Изменения на текущей неделе [вкл]",
                       callback_data=NotificationsFab(action="pressed_current_week_change"))
    else:
        builder.button(text="🔕 Изменения на текущей неделе [выкл]",
                       callback_data=NotificationsFab(action="pressed_current_week_change"))

    if notifications[1]:
        builder.button(text="🔔 Расписание на след. неделю [вкл]",
                       callback_data=NotificationsFab(action="pressed_sch_next_week"))
    else:
        builder.button(text="🔕 Расписание на след. неделю [выкл]",
                       callback_data=NotificationsFab(action="pressed_sch_next_week"))

    if notifications[2]:
        builder.button(text="🔔 Пары на сегодня [вкл]",
                       callback_data=NotificationsFab(action="pressed_get_sch_today"))
    else:
        builder.button(text="🔕 Пары на сегодня [выкл]",
                       callback_data=NotificationsFab(action="pressed_get_sch_today"))

    builder.button(text="↩ Вернуться в меню",
                   callback_data=NotificationsFab(action="pressed_back"))

    # Выравниваем кнопки по 1 в ряд
    builder.adjust(1)

    return builder.as_markup()
