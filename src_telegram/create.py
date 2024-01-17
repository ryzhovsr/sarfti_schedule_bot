import aiogram
import config

from aiogram import Dispatcher
from scripts.user_db import UserDatabase
from scripts.schedule_data import ScheduleData

dp = Dispatcher()
bot = aiogram.Bot(token=config.bot_token)
user_db = UserDatabase()
sch = ScheduleData()
