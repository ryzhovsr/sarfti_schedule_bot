import contextlib

from aiogram import types


async def delete_current_message_from_user(message: types.Message):
    """Удаляет текущее сообщение пользователя"""
    with contextlib.suppress(Exception):
        await message.bot.delete_message(message.chat.id, message.message_id)


async def delete_last_message_from_db(bot, message_id, cursor):
    """Удаляет последнее сообщение из чата пользователя в БД"""
    cursor.execute(f"SELECT * FROM users "
                   f"WHERE user_id = {message_id}")
    user_data = cursor.fetchone()
    with contextlib.suppress(Exception):
        await bot.delete_message(user_data[0], user_data[1])


async def delete_message(bot, user_data):
    """Удаляет сообщение пользователя по заданному id чата и id сообщение"""
    with contextlib.suppress(Exception):
        await bot.delete_message(user_data[0], user_data[1])


async def modify_message(bot):
    with contextlib.suppress(Exception):
        pass
