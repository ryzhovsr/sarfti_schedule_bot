from vkbottle import Keyboard, Callback


def get_keyboard():
    return ((Keyboard(inline=True)
             .add(Callback("Вернутся к выбору", {"start_menu": "back"})))
            .get_json())


def get_text(is_teacher):
    return "Ничего не найдено 😕\n Попробуйте ввести" + (
        " ФИО преподавателя " if is_teacher == 1 else " название группы ") + "ещё раз."
