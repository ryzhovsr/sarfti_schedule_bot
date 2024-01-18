from schedule.schedule_data import ScheduleData
from src_vk.keyboards.search_kb import SearchKeyboard
from src_vk.scripts.user_db import UserDatabase

# Инициализируем расписание, базу данных и книжку поиска
sch = ScheduleData("src_vk")
user_db = UserDatabase()
search_kb = SearchKeyboard()
