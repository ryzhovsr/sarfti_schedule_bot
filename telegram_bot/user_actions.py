import config
from aiogram.types import FSInputFile
from aiogram import types
from datetime import datetime

import codecs
import os
import sys


def write_user_action(message: types.Message = None, callback: types.CallbackQuery = None,
                      action: str = "", directory: str = "src_telegram"):
    current_time = datetime.now()

    if os.name == 'nt':
        journal_dir = os.path.join(os.getcwd(), directory + "\\data\\user_actions.txt")
    else:
        journal_dir = os.path.join(os.getcwd(), directory + "/data/user_actions.txt")

    with codecs.open(journal_dir, 'a', encoding='utf-8') as f:  # a - ключ добавления в файл
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


def restart():
    print("Обновление потока")
    os.execv(sys.executable, ['python'] + sys.argv)
