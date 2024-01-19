import os
import sqlite3

from vkbottle.bot import Message


class UserDatabase:
    """
     Класс содержит базу данных пользователей:
     id пользователя, его последнее id сообщения в чате и
     текущий выбор группы/ФИО преподавателя
     """

    def __init__(self):
        # Смотрим под чем исполняется скрипт, и указываем правильный путь
        if os.name == 'nt':
            self.__db_path = os.path.join(os.getcwd(), 'src_vk\\data\\')
        else:
            self.__db_path = os.path.join(os.getcwd(), 'src_vk/data/')

        # Если директории data нет в проекте, создаём её
        if not os.path.exists(self.__db_path):
            os.makedirs(self.__db_path)
        self.__connect = sqlite3.connect(self.__db_path + "users.db")
        self.__cursor = self.__connect.cursor()
        self.__cursor.execute("CREATE TABLE IF NOT EXISTS users"
                              "(user_id INTEGER PRIMARY KEY, "
                              "message_id INTEGER, "
                              "is_teacher BOOLEAN, "
                              "current_selection VARCHAR(15));")

        self.__cursor.execute("CREATE TABLE IF NOT EXISTS notifications"
                              "(user_id INTEGER PRIMARY KEY, "
                              "is_note_current_week_changes BOOL DEFAULT 0, "
                              "is_note_new_schedule BOOL DEFAULT 0, "
                              "is_note_classes_today BOOL DEFAULT 0, "
                              "FOREIGN KEY (user_id) REFERENCES users (user_id));")

        self.__connect.commit()

    def is_user_exists(self, user_id: int):
        """Проверяет существует ли пользователь в БД"""
        self.__cursor.execute(f"SELECT * FROM users "
                              f"WHERE user_id = {user_id};")
        return self.__cursor.fetchone()

    def update_user_message_id(self, message: Message):
        """Обновляет id сообщения бота"""
        if self.is_user_exists(message.peer_id) is None:
            self.__cursor.execute(f"INSERT INTO users(user_id, message_id) "
                                  f"VALUES({message.peer_id}, {message.message_id});")
            self.__cursor.execute(f"INSERT INTO notifications(user_id) "
                                  f"VALUES({message.peer_id});")
        else:
            self.__cursor.execute(f"UPDATE users "
                                  f"SET message_id = ({message.message_id}) "
                                  f"WHERE user_id = ({message.peer_id});")
            self.__cursor.execute(f"UPDATE notifications "
                                  f"SET user_id = ({message.peer_id}) "
                                  f"WHERE user_id = ({message.peer_id});")

        self.__connect.commit()

    def update_user_is_teacher(self, user_id: int, is_teacher: int):
        """Обновляет выбор (преподаватель или группа) пользователя"""
        self.__cursor.execute("UPDATE users SET is_teacher = ? "
                              "WHERE user_id = ?", (is_teacher, user_id))

        self.__connect.commit()

    def update_user_current_selection(self, user_id: int, current_selection: str):
        """Обновляет текущий выбор пользователя"""
        self.__cursor.execute("UPDATE users SET current_selection = ? "
                              "WHERE user_id = ?", (current_selection, user_id))
        self.__connect.commit()

    def get_cursor(self):
        return self.__cursor

    def get_last_message_id(self, user_id: int) -> int:
        """Возвращает id последнего сообщения у бота"""
        self.__cursor.execute(f"SELECT message_id FROM users WHERE user_id = {user_id}")

        # Возвращаем нулевой элемент - там будет содержаться последний id сообщения данного пользователя
        return self.__cursor.fetchone()[0]

    def get_user_is_teacher(self, user_id: int) -> int:
        """Возвращает выбор (преподаватель или группа) у пользователя"""
        self.__cursor.execute(f"SELECT is_teacher FROM users WHERE user_id = {user_id}")

        return self.__cursor.fetchone()[0]

    def get_user_current_selection(self, user_id: int) -> str:
        """Возвращает текущий выбор у пользователя"""
        self.__cursor.execute(f"SELECT current_selection FROM users WHERE user_id = {user_id}")

        return self.__cursor.fetchone()[0]

    def get_user_notification(self, user_id: int):
        """Возвращает выбранные уведомления пользователя"""
        self.__cursor.execute(f"SELECT * FROM notifications WHERE user_id = {user_id}")
        user_notifications_data = self.__cursor.fetchone()
        return [user_notifications_data[1], user_notifications_data[2], user_notifications_data[3]]

    def is_user_notification_enabled(self, user_id: int):
        """Возвращает true, если у пользователя включено хотя бы 1 уведомление"""
        self.__cursor.execute(f"SELECT * FROM notifications WHERE user_id = {user_id}")
        user_notifications_data = self.__cursor.fetchone()
        return user_notifications_data[1] == 1 or user_notifications_data[2] == 1 or user_notifications_data[3] == 1

    def update_is_note_current_week_changes(self, user_id: int, notification: bool):
        self.__cursor.execute("UPDATE notifications SET is_note_current_week_changes = ? "
                              "WHERE user_id = ?", (notification, user_id))
        self.__connect.commit()

    def update_is_note_new_schedule(self, user_id: int, notification: bool):
        self.__cursor.execute("UPDATE notifications SET is_note_new_schedule = ? "
                              "WHERE user_id = ?", (notification, user_id))
        self.__connect.commit()

    def update_is_note_classes_today(self, user_id: int, notification: bool):
        self.__cursor.execute("UPDATE notifications SET is_note_classes_today = ? "
                              "WHERE user_id = ?", (notification, user_id))
        self.__connect.commit()
