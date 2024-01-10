import os
import requests
import pandas as pd
import contextlib
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from io import StringIO


class ScheduleData:
    def __init__(self):
        self.__groups = {}      # Список групп и их group_id
        self.__teachers = {}    # Список преподавателей и их teacher_id
        self.__places = {}      # Список аудиторий и их place_id
        self.__dates = {}       # Список учебных недель и их date_id

        self.__current_week_id = {}            # id текущей (рабочей) недели
        self.__schedule_current_week = {}      # Расписание текущей (рабочей) недели
        self.__schedule_current_week_dir = ''  # Путь к директории для файла с расписанием

        self.__class_time_weekdays = {}  # Время учебных занятий в будни (понедельник – пятница)
        self.__class_time_saturday = {}  # Время учебных занятий в субботу

        self.__html_data_sarfti_schedule = ''  # Страница расписания СарФТИ c исходным html кодом
        self.__html_soup_sarfti_schedule = ''  # Разобранная html страница расписания СарФТИ

        # Смотрим под чем исполняется скрипт, и указываем правильный путь
        if os.name == 'nt':
            __schedule_current_week_dir = os.path.join(os.getcwd(), 'Data\\schedule_current_week.h5')
        else:
            __schedule_current_week_dir = os.path.join(os.getcwd(), 'Data/schedule_current_week.h5')

    def __load_main_data(self):
        """Парсит списки групп, преподавателей, аудиторий и недель c сайта СарФТИ"""
        with contextlib.suppress(Exception):
            # Берём страницу с расписанием СарФТИ
            __html_data_sarfti_schedule = requests.post('https://sarfti.ru/?page_id=20',
                                                        data={'page_id': '20', 'view': 'Просмотр'}).text

            # Разбираем страницу
            __html_soup_sarfti_schedule = BeautifulSoup(__html_data_sarfti_schedule, 'lxml')

            # Получаем сырые данные групп, преподавателей, мест (аудиторий) и дат
            groups_raw_data = [i.findAll('option') for i in
                               __html_soup_sarfti_schedule.findAll('select', attrs={'name': 'group_id'})]
            teachers_raw_data = [i.findAll('option') for i in
                                 __html_soup_sarfti_schedule.findAll('select', attrs={'name': 'teacher_id'})]
            places_raw_data = [i.findAll('option') for i in
                               __html_soup_sarfti_schedule.findAll('select', attrs={'name': 'place_id'})]
            dates_raw_data = [i.findAll('option') for i in
                              __html_soup_sarfti_schedule.findAll('select', attrs={'name': 'date_id'})]

            # Получаем время занятий на будние дни
            for item in __html_soup_sarfti_schedule.findAll('table',
                                                            attrs={'style': 'width: 274px; border-style: none;'}):
                __class_time_weekdays = dict(x.split('=') for x in item.text.
                                             replace('\n\n\n1 пара', '1 пара').
                                             replace('\xa0', ' ').
                                             replace('\n\n\n', ';').
                                             replace('\n–\n', '=').
                                             replace('\n', ' | ')[:-1].split(';'))
                break

            # Получаем время занятий на субботу
            for item in __html_soup_sarfti_schedule.findAll('table', attrs={'style': 'width: 273px; border: none;'}):
                __class_time_saturday = dict(x.split('=') for x in item.text.
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

    def __calc_current_week(self):
        """Вычисляет текущую неделю"""
        time_now = datetime.now()
        for week_id in list(self.__dates):
            if (pd.to_datetime(self.__dates[week_id]) - timedelta(days=1) <= time_now <
                    pd.to_datetime(self.__dates[week_id]) + timedelta(days=7)):
                # __current_week_id = pd.to_datetime(self.__dates[week_id]).strftime('%Y-%m-%d')
                __current_week_id = week_id
                break

    def __calc_schedule_current_week(self):
        """Вычисляет расписание на текущую неделю"""
        # Данные сайта по управлению расписанием
        schedule_management_html = requests.post('http://scs.sarfti.ru/login/index',
                                                 data={'login': '', 'password': '', 'guest': 'Войти+как+Гость'})

        # Данные сайта по печати (вывода) расписания на текущую неделю
        current_week_schedule_html = requests.post('http://scs.sarfti.ru/date/printT',
                                                   data={'id': self.__current_week_id, 'show': 'Распечатать',
                                                         'list': 'list', 'compact': 'compact'},
                                                   cookies=schedule_management_html.history[0].cookies)

        current_week_schedule_html.encoding = 'utf-8'

        for item in pd.read_html(StringIO(current_week_schedule_html.text)):
            if 'День' and 'Пара' in item:
                with contextlib.suppress(Exception):
                    os.remove(self.__schedule_current_week_dir)

                file = pd.HDFStore(self.__schedule_current_week_dir)
                file[str(self.__current_week_id)] = item
                file.close()
                __schedule_current_week = item
                break

    def update_schedule(self):
        """Обновляет расписание"""
        self.__load_main_data()
        self.__calc_current_week()
        self.__calc_schedule_current_week()
