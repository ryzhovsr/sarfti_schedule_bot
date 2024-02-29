import contextlib

from aiogram import types


async def delete_current_message_from_user(message: types.Message):
    """Удаляет текущее сообщение пользователя"""
    with contextlib.suppress(Exception):
        await message.bot.delete_message(message.chat.id, message.message_id)


async def delete_last_message_from_db(bot, message_id, cursor):
    """Удаляет последнее сообщение из чата пользователя в БД"""
    cursor.execute(f"SELECT * FROM users WHERE user_id = {message_id}")
    user_data = cursor.fetchone()
    with contextlib.suppress(Exception):
        await bot.delete_message(user_data[0], user_data[1])


async def delete_message(bot, user_data):
    """Удаляет сообщение пользователя по заданному id чата и id сообщения"""
    with contextlib.suppress(Exception):
        await bot.delete_message(chat_id=user_data[0], message_id=user_data[1])


async def modify_message(bot, chat_id: int, message_id: int, text: str, reply_markup=None, parse_mode=None):
    """Редактирует сообщение"""
    return await bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, parse_mode=parse_mode)
    #with contextlib.suppress(Exception):



async def delete_notes(bot, chat_id: int, user_db):
    """Удаляет уведомления у пользователя"""
    # id уведомлений пользователя
    id_note_one = user_db.get_id_notes_one(user_id=chat_id)
    id_note_two = user_db.get_id_notes_two(user_id=chat_id)

    # Если id первого уведомления не равен 0
    if id_note_one[1]:
        await delete_message(bot, id_note_one)
        user_db.update_id_note_current_week(user_id=chat_id, note_id=0)
    # Если id второго уведомления не равен 0
    if id_note_two[1]:
        await delete_message(bot, id_note_two)
        user_db.update_id_note_new_schedule(user_id=chat_id, note_id=0)
