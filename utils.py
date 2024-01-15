async def find_coincidence_in_list(mes_text, roster, prefix=""):
    """Находит совпадения сообщения в списке roster"""
    mes_text_with_dash = await add_dash_in_group(mes_text)
    result_roster = {}

    for roster_key in roster:
        if (roster[roster_key].lower().startswith(mes_text.lower()) or
                roster[roster_key].lower().startswith(mes_text_with_dash.lower())):
            result_roster[roster_key + prefix] = roster[roster_key]
    return result_roster


async def find_coincidence_group_teacher(mes_text, schedule):
    """Находит совпадение сообщения с группами и ФИО преподавателей"""
    all_coincidence = [await find_coincidence_in_list(mes_text, schedule.get_groups()),
                       await find_coincidence_in_list(mes_text, schedule.get_teachers())]
    return all_coincidence


async def add_dash_in_group(text):
    """Вовзращает текст с тире между символом и цифрой для корректного нахождения сопоставлений групп"""
    position = 0

    for char in text:
        position += 1

        if not char.isalpha() and char.isnumeric():
            text = text[:position - 1] + '-' + text[position - 1:]
            break

    return text


def define_goup_or_teacher(text):
    """
    Проверяет преподаватель в text или нет по точке
    в конце предложения (инициалы преподавателя).
    Возвращает текст с подписью
    """
    if text.endswith("."):
        text = f"👥 Преподаватель {text}"
    else:
        text = f"👥 Группа {text}"

    return text
