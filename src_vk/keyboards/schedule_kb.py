from vkbottle import Keyboard, Callback

from src_vk.create import sch


def get_keyboard():
    """Возвращает клавиатуру для расписания"""
    return (Keyboard(inline=True)
            .add(Callback("❓ Информация", {"schedule": "info"}))
            .add(Callback("🕘 Пары", {"schedule": "time"})).row()
            .add(Callback("↩ Вернуться в меню", {"schedule": "back"}))
            ).get_json()


def get_keyboard_after_press_time():
    """Возвращает клавиатуру для пар"""
    return (Keyboard(inline=True)
            .add(Callback("❓ Информация", {"schedule": "info"}))
            .add(Callback("🔼 Расписание", {"main_menu": "current_week"})).row()
            .add(Callback("↩ Вернуться в меню", {"schedule": "back"}))
            ).get_json()


def get_keyboard_after_press_info():
    """Возвращает клавиатуру для информации"""
    return (Keyboard(inline=True)
            .add(Callback("🔼 Расписание", {"main_menu": "current_week"}))
            .add(Callback("🕘 Пары", {"schedule": "time"})).row()
            .add(Callback("↩ Вернуться в меню", {"schedule": "back"}))
            ).get_json()


def get_keyboard_next_week(dict_weeks: dict):
    """Возвращает клавиатуру для следующих недель"""
    keyboard = Keyboard(inline=True)

    for i in range(len(dict_weeks)):
        keyboard.add(Callback(f"📅 {list(dict_weeks.values())[i]}",
                              {"week_selection": f"{list(dict_weeks.keys())[i]}"}))

        if (i + 1) % 2 == 0:
            keyboard.row()

    if len(dict_weeks) % 2 != 0:
        keyboard.row()

    keyboard.add(Callback("↩ Вернуться в меню", {"schedule": "back"})).get_json()

    return keyboard


def get_text_time():
    """Возвращает текст для пар"""
    text_out = "🕘 Расписание пар.\n\n" + \
               "🔹 ПОНЕДЕЛЬНИК - ПЯТНИЦА:\n"

    one = u"\u0031\ufe0f\u20e3"
    two = u"\u0032\ufe0f\u20e3"
    three = u"\u0033\ufe0f\u20e3"
    four = u"\u0034\ufe0f\u20e3"
    five = u"\u0035\ufe0f\u20e3"
    six = u"\u0036\ufe0f\u20e3"
    seven = u"\u0037\ufe0f\u20e3"

    for item in sch.get_class_time_weekdays().items():
        match item[0]:
            case "1":
                text_out += one
            case "2":
                text_out += two
            case "3":
                text_out += three
            case "4":
                text_out += four
            case "5":
                text_out += five
            case "6":
                text_out += six
            case "7":
                text_out += seven

        text_out += " " + item[1] + "\n"

    text_out += "\n🔹 СУББОТА:\n"

    for item in sch.get_class_time_saturday().items():
        match item[0]:
            case "1":
                text_out += one
            case "2":
                text_out += two
            case "3":
                text_out += three
            case "4":
                text_out += four

        text_out += " " + item[1] + "\n"

    return text_out


def get_text_info():
    """Возвращает текст для информации"""
    return "Что означают значки в расписании занятий:\n\n" + \
        u"\u0031\ufe0f\u20e3 - номер пары\n" + \
        "💬 - лекция\n" + \
        "🔥 - практика, лаб. работа\n" + \
        "📡 - онлайн\n" + \
        "🅰 - подгруппа 1\n" + \
        "🅱 - подгруппа 2"
