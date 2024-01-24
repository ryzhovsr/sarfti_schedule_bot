from common_modules.schedule_data import ScheduleData
from src_vk.keyboards.search_kb import SearchKeyboard
from src_vk.scripts.user_db import UserDatabase

# Инициализируем расписание, базу данных и книжку поиска
user_db = UserDatabase()
sch = ScheduleData("src_vk")
search_kb = SearchKeyboard()
