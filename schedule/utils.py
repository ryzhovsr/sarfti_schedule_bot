from src_telegram import config
from aiogram.types import FSInputFile
from aiogram import types
from datetime import datetime

import codecs
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


# Записывает в журнал все действия пользователей
def write_user_action(message: types.Message = None, callback: types.CallbackQuery = None,
                      action: str = "", directory: str = "src_telegram"):
    current_time = datetime.now()

    if os.name == 'nt':
        journal_dir = os.path.join(os.getcwd(), directory + "\\data\\user_actions.txt")
    else:
        journal_dir = os.path.join(os.getcwd(), directory + "/data/user_actions.txt")

    with codecs.open(journal_dir, 'a', encoding='utf-8') as f:   # a - ключ добавления в файл
        if message is not None:
            f.write(str(current_time)[:19] +
                    f" | full_name = {message.from_user.full_name}" +
                    f" | login = {message.chat.username}" +
                    f" | ID = {str(message.from_user.id)}" +
                    f" | action = {action}\n")
        elif callback is not None:
            f.write(str(current_time)[:19] +
                    f" | full_name = {callback.from_user.full_name}" +
                    f" | login = {callback.from_user.username}" +
                    f" | ID = {str(callback.from_user.id)}" +
                    f" | action = {action}\n")


async def check_key(message: types.Message, directory: str = "src_telegram"):
    if os.name == 'nt':
        journal_dir = os.path.join(os.getcwd(), directory + "\\data\\user_actions.txt")
    else:
        journal_dir = os.path.join(os.getcwd(), directory + "/data/user_actions.txt")

    admins = config.admin_list

    for admin_id in admins:
        if message.from_user.id == admin_id:
            file = FSInputFile(journal_dir)
            await message.answer_document(file)
            return True

    return False
