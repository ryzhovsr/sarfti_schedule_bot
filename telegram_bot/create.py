"""Модуль создаёт основные переменные для взаимодействия"""

from config import bot_token_tg
from aiogram import Dispatcher, Bot
from user_db import UserDatabase
from common_modules.schedule_data import ScheduleData


dp = Dispatcher()
bot = Bot(token=bot_token_tg)
user_db = UserDatabase()
sch = ScheduleData()
