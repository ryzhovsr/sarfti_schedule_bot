import sqlite3

from vkbottle.bot import Message


class UserDatabase:
    """Класс содержит id пользователей и их id последнего сообщения в чате"""
    def __init__(self):
        self.__connect = sqlite3.connect("vk_users.db")
        self.__cursor = self.__connect.cursor()
        self.__cursor.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER, message_id INTEGER)")
        self.__connect.commit()

    def is_user_exists(self, user_id):
        """Проверяет существует ли пользователь в БД"""
        self.__cursor.execute(f"SELECT * FROM users "
                              f"WHERE user_id = {user_id}")
        return self.__cursor.fetchone()

    def update_user_message_id(self, message: Message):
        """Обновляет id сообщения пользователя"""
        if self.is_user_exists(message.peer_id) is None:
            self.__cursor.execute(f"INSERT INTO users(user_id, message_id) "
                                  f"VALUES({message.peer_id}, {message.message_id});")
        else:
            self.__cursor.execute(f"UPDATE users "
                                  f"SET message_id = ({message.message_id}) "
                                  f"WHERE user_id = ({message.peer_id});")

        self.__connect.commit()

    def get_cursor(self):
        return self.__cursor

    def get_last_message_id(self, user_id):
        """Возвращает id последнего сообщения у пользователя"""
        self.__cursor.execute(f"SELECT message_id FROM users "
                              f"WHERE user_id = {user_id}")

        # Возвращаем нулевой элемент - там будет содержаться последний id сообщения данного пользователя
        return self.__cursor.fetchone()[0]
