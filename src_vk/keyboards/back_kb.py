from vkbottle import Keyboard, Callback


def get_keyboard() -> str:
    """Возвращаем клавиатуру, которая содержит кнопку выхода к начальному меню"""
    return (Keyboard(inline=True)
            .add(Callback("↩ Вернутся к выбору", {"start_menu": "back"}))
            ).get_json()


def get_text(is_teacher: int) -> str:
    """Возвращаем текст, относительно от выбора пользователя"""
    return "Ничего не найдено 😕\nПопробуйте ввести" + (
        " ФИО преподавателя " if is_teacher == 1 else " название группы ") + "ещё раз."
