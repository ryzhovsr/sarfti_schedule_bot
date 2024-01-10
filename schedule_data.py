import os
import requests
import contextlib
import time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from io import StringIO


class ScheduleData:
    def __init__(self):
        self.__groups = {}      # Группы
        self.__teachers = {}    # Преподаватели
        self.__places = {}      # Аудитории
        self.__dates = {}       # Учебные недели

        self.__current_week_id = ''            # id текущей (рабочей) недели
        self.__week_ids = []                   # id всех доступные недель
        self.__schedule_current_week = {}      # Расписание текущей (рабочей) недели
        self.__schedule_week_dir = ''  # Путь к директории для файла с расписанием

        self.__class_time_weekdays = {}  # Время учебных занятий в будни (понедельник – пятница)
        self.__class_time_saturday = {}  # Время учебных занятий в субботу

        self.__html_data_sarfti_schedule = ''  # Страница расписания СарФТИ c исходным html кодом
        self.__html_soup_sarfti_schedule = ''  # Разобранная html страница расписания СарФТИ

        # Смотрим под чем исполняется скрипт, и указываем правильный путь
        if os.name == 'nt':
            self.__schedule_week_dir = os.path.join(os.getcwd(), 'Data\\schedule_current_week.h5')
        else:
            self.__schedule_week_dir = os.path.join(os.getcwd(), 'Data/schedule_current_week.h5')

    def __load_main_data(self):
        """Парсит списки групп, преподавателей, аудиторий и недель c сайта СарФТИ"""
        with contextlib.suppress(Exception):
            # Берём страницу с расписанием СарФТИ
            self.__html_data_sarfti_schedule = requests.post('https://sarfti.ru/?page_id=20',
                                                             data={'page_id': '20', 'view': 'Просмотр'}).text

            # Разбираем страницу
            self.__html_soup_sarfti_schedule = BeautifulSoup(self.__html_data_sarfti_schedule, 'lxml')

            # Получаем сырые данные групп, преподавателей, мест (аудиторий) и дат
            groups_raw_data = [i.findAll('option') for i in
                               self.__html_soup_sarfti_schedule.findAll('select', attrs={'name': 'group_id'})]
            teachers_raw_data = [i.findAll('option') for i in
                                 self.__html_soup_sarfti_schedule.findAll('select', attrs={'name': 'teacher_id'})]
            places_raw_data = [i.findAll('option') for i in
                               self.__html_soup_sarfti_schedule.findAll('select', attrs={'name': 'place_id'})]
            dates_raw_data = [i.findAll('option') for i in
                              self.__html_soup_sarfti_schedule.findAll('select', attrs={'name': 'date_id'})]

            # Получаем время занятий на будние дни
            for item in self.__html_soup_sarfti_schedule.findAll('table',
                                                                 attrs={'style': 'width: 274px; border-style: none;'}):
                self.__class_time_weekdays = dict(x.split('=') for x in item.text.
                                                  replace('\n\n\n1 пара', '1 пара').
                                                  replace('\xa0', ' ').
                                                  replace('\n\n\n', ';').
                                                  replace('\n–\n', '=').
                                                  replace('\n', ' | ')[:-1].split(';'))
                break

            # Получаем время занятий на субботу
            for item in self.__html_soup_sarfti_schedule.findAll('table',
                                                                 attrs={'style': 'width: 273px; border: none;'}):
                self.__class_time_saturday = dict(x.split('=') for x in item.text.
                                                  replace('\n\n\n1 пара', '1 пара').
                                                  replace('\xa0', ' ').
                                                  replace('\n\n\n', ';').
                                                  replace('\n–\n', '=').
                                                  replace('\n', ' | ')[:-1].split(';'))
                break

            # Прогоняем цикл по всем сырым данным групп, преподавателей, мест (аудиторий) и дат
            for item in [groups_raw_data, teachers_raw_data, places_raw_data, dates_raw_data]:
                for i in range(0, item[0].__len__()):
                    # Если элемент не содержит "Выберите", то загоняем его в соответствующий список
                    if 'Выберите' not in item[0][i].text:
                        if item == groups_raw_data:
                            self.__groups[item[0][i].attrs['value']] = item[0][i].text
                        if item == teachers_raw_data:
                            self.__teachers[item[0][i].attrs['value']] = item[0][i].text
                        if item == places_raw_data:
                            self.__places[item[0][i].attrs['value']] = item[0][i].text
                        if item == dates_raw_data:
                            self.__dates[item[0][i].attrs['value']] = item[0][i].text

    def __cal_current_week(self):
        """Вычисляет текущую неделю"""
        time_now = datetime.now()
        self.__week_ids = []
        for week_id in list(self.__dates):
            self.__week_ids.append(week_id)
            if (pd.to_datetime(self.__dates[week_id]) - timedelta(days=1) <= time_now <
                    pd.to_datetime(self.__dates[week_id]) + timedelta(days=7)):
                # __current_week_id = pd.to_datetime(self.__dates[week_id]).strftime('%Y-%m-%d')
                self.__current_week_id = week_id
                break

    def __parse_schedule_week(self, week_id):
        """Возвращает распиисание по заданному id недели"""
        # Данные сайта по управлению расписанием
        schedule_management_html = requests.post('http://scs.sarfti.ru/login/index',
                                                 data={'login': '', 'password': '', 'guest': 'Войти+как+Гость'})

        # Данные сайта по печати (вывода) расписания на текущую неделю
        current_week_schedule_html = requests.post('http://scs.sarfti.ru/date/printT',
                                                   data={'id': week_id, 'show': 'Распечатать',
                                                         'list': 'list', 'compact': 'compact'},
                                                   cookies=schedule_management_html.history[0].cookies)

        current_week_schedule_html.encoding = 'utf-8'

        for item in pd.read_html(StringIO(current_week_schedule_html.text)):
            if 'День' and 'Пара' in item:
                file = pd.HDFStore(self.__schedule_week_dir)
                file['_' + week_id] = item # ошибка PerformanceWarning это предупреждение о том что есть таблица  которая будет грузить медленнее чем другие из-за формата данных. Ошибка возникает не на всех неделях
                file.close()
                self.__schedule_current_week = item
                break

    def update_schedule(self):
        """Обновляет расписание"""
        self.__load_main_data()
        self.__cal_current_week()
        self.__load_schedule()

    def __del_store(self):
        """Удаление старого файла с расписанием"""
        with contextlib.suppress(Exception):
            os.remove(self.__schedule_week_dir)

    def __load_schedule(self):
        """Загружает в файл расписание для актуальной и более новых недель"""
        self.__del_store()
        for week in self.__week_ids:
            pass
            self.__parse_schedule_week(week)

    def run_updates(self, iterations_between_updates=30, sleep_time=120):
        """Запускает обновление основных данных и парсер расписания
        iterations_between_updates=30 и sleep_time=120 - будет обновляться база каждый день, а расписание каждые 2 мин
        """
        while True:
            self.__load_main_data()
            time.sleep(sleep_time)
            for i in range(iterations_between_updates):
                self.__parse_schedule_week(self.__load_schedule())
                time.sleep(sleep_time)

    def get_week_schedule(self, week_num):
        """Возвращает расписание на неделю по week_num, где 0 - текущая, 1 - следующ. ..."""
        week = '_' + str(int(self.__current_week_id) + week_num)
        file = pd.HDFStore(self.__schedule_week_dir)
        res_week = file[week]  # Ошибка PerformanceWarning это предупреждение о том, что есть таблица которая будет грузить медленнее чем другие из-за формата данных. Ошибка возникает не на всех неделях
        file.close()
        return res_week

    def get_dates(self):
        """Возвращает учебные недели"""
        return self.__dates

    def get_groups(self):
        """Возвращает группы"""
        return self.__groups

    def get_schedule_week_dir(self):
        """Возвращает путь к директории для файла с расписанием"""
        return self.__schedule_week_dir

    def get_class_time_saturday(self):
        """Возвращает время учебных занятий в субботу"""
        return self.__class_time_saturday

    def get_class_time_weekdays(self):
        """Возвращает время учебных занятий в будни (понедельник – пятница)"""
        return self.__class_time_weekdays

    def get_current_week_id(self):
        """Возвращает id текущей недели"""
        return self.__current_week_id


if __name__ == "__main__":
    schedule = ScheduleData()
    # schedule._cal_current_week()
    # schedule._get_week_chedule(schedule.get_week())
    schedule.update_schedule()
    # print(schedule.get_week_schedule(0)) # вытаскивание расписание недели
