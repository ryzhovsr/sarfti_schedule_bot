"""Модуль создаёт основные переменные для взаимодействия"""

from config import bot_token_tg
from aiogram import Dispatcher, Bot
from user_db import UserDatabase
from schedule_data import ScheduleData

# Объект, отвечающий за обработку входящих сообщений и других обновлений, поступающих от телеграма
dp = Dispatcher()

# Объект телеграм бота
bot = Bot(token=bot_token_tg)

# Объект базы данных пользователей
user_db = UserDatabase()

# Объект расписания
sch = ScheduleData()
