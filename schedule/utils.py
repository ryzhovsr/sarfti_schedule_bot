import os


def find_coincidence_in_list(mes_text, roster, prefix=""):
    """Находит совпадения сообщения в списке roster"""
    result_roster = {}

    for roster_key in roster:
        if (roster[roster_key].lower().startswith(mes_text.lower()) or
                roster[roster_key].lower().startswith(mes_text.lower())):
            result_roster[roster_key + prefix] = roster[roster_key]
    return result_roster


def find_coincidence_group_teacher(mes_text, schedule):
    """Находит совпадение сообщения с группами и ФИО преподавателей"""
    all_coincidence = [find_coincidence_in_list(mes_text, schedule.get_groups()),
                       find_coincidence_in_list(mes_text, schedule.get_teachers())]
    return all_coincidence


def add_dash_in_group(text: str):
    """Возвращает текст с тире между символом и цифрой для корректного нахождения сопоставлений групп"""

    if "-" in text:
        return text

    position = 0

    for char in text:
        position += 1

        if not char.isalpha() and char.isnumeric():
            text = text[:position - 1] + '-' + text[position - 1:]
            break

    return text


def add_sign_group_or_teacher(data: str):
    """Добавляет к строке подпись "👥 Преподаватель" или "👥 Группа"."""
    if is_teacher(data):
        data = f"👤 Преподаватель {data}"
    else:
        data = f"👤 Группа {data}"

    return data


def is_teacher(data: str):
    """Проверяет это группа эли преподаватель"""
    return data.endswith(".")


def restore_user_action(directory: str = "src_telegram"):
    if os.name == 'nt':
        journal_dir = os.path.join(os.getcwd(), directory + "\\data\\user_actions.txt")
    else:
        journal_dir = os.path.join(os.getcwd(), directory + "/data/user_actions.txt")

    open(journal_dir, 'w').close()

    return False
