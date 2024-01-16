import sqlite3
import os

from aiogram import types


class UserDatabase:
    """
    Класс содержит базу данных пользователей:
    id пользователя, его последнее id сообщения в чате и
    текущий выбор группы/ФИО преподавателя
    """
    def __init__(self):
        # Смотрим под чем исполняется скрипт, и указываем правильный путь
        if os.name == 'nt':
            self.__db_path = os.path.join(os.getcwd(), 'data\\')
        else:
            self.__db_path = os.path.join(os.getcwd(), 'data/')

        # Если директории data нет в проекте, создаём её
        if not os.path.exists(self.__db_path):
            os.makedirs(self.__db_path)

        self.__connect = sqlite3.connect(self.__db_path + "users.db")
        self.__cursor = self.__connect.cursor()
        self.__cursor.execute("CREATE TABLE IF NOT EXISTS users"
                              "(user_id INTEGER PRIMARY KEY, "
                              "message_id INTEGER, "
                              "current_selection VARCHAR(15));")

        self.__cursor.execute("CREATE TABLE IF NOT EXISTS notifications"
                              "(user_id INTEGER PRIMARY KEY, "
                              "is_note_current_week_changes BOOL DEFAULT 0, "
                              "is_note_new_schedule BOOL DEFAULT 0, "
                              "is_note_classes_today BOOL DEFAULT 0, "
                              "FOREIGN KEY (user_id) REFERENCES users (user_id));")

        self.__connect.commit()

    def is_user_exists(self, user_id):
        """Проверяет существует ли пользователь в БД"""
        self.__cursor.execute(f"SELECT * FROM users WHERE user_id = {user_id};")
        return self.__cursor.fetchone()

    def update_user_message_id(self, message: types.Message):
        """Обновляет id сообщения пользователя"""
        if self.is_user_exists(message.chat.id) is None:
            self.__cursor.execute(f"INSERT INTO users(user_id, message_id) "
                                  f"VALUES({message.chat.id}, {message.message_id});")
            self.__cursor.execute(f"INSERT INTO notifications(user_id) "
                                  f"VALUES({message.chat.id});")
        else:
            self.__cursor.execute(f"UPDATE users "
                                  f"SET message_id = ({message.message_id}) "
                                  f"WHERE user_id = ({message.chat.id});")
            self.__cursor.execute(f"UPDATE notifications "
                                  f"SET user_id = ({message.chat.id}) "
                                  f"WHERE user_id = ({message.chat.id});")

        self.__connect.commit()

    def update_user_current_selection(self, user_id, selection):
        """Обновляет текущий выбор пользователя в меню (группа/ФИО преподавателя)"""
        self.__cursor.execute("UPDATE users SET current_selection = ? "
                              "WHERE user_id = ?", (selection, user_id))
        self.__connect.commit()

    def get_cursor(self):
        return self.__cursor

    def get_last_message_id(self, user_id):
        """Возвращает id последнего сообщения пользователя"""
        self.__cursor.execute(f"SELECT message_id FROM users WHERE user_id = {user_id}")
        # Возвращаем нулевой элемент - там будет содержаться последний id сообщения данного пользователя
        return self.__cursor.fetchone()[0]

    def get_user_current_selection(self, user_id):
        """Возвращает текущий выбор пользователя в меню (группа/ФИО преподавателя)"""
        self.__cursor.execute(f"SELECT current_selection FROM users WHERE user_id = {user_id}")
        # Возвращаем нулевой элемент - там будет содержаться текущий выбор пользователя
        return self.__cursor.fetchone()[0]

    def is_user_notification_enabled(self, user_id: int):
        """Возвращает true, если у пользователя включено хотя бы 1 уведомление"""
        self.__cursor.execute(f"SELECT * FROM notifications WHERE user_id = {user_id}")
        user_notifications_data = self.__cursor.fetchone()
        return user_notifications_data[1] == 1 or user_notifications_data[2] == 1 or user_notifications_data[3] == 1

