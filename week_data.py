import os
import time
import requests
from bs4 import BeautifulSoup
import datetime
from datetime import datetime, timedelta
import pandas as pd
from io import StringIO



class ScheduleData:
    def __init__(self):
        # Все переменные ниже необходимы для работы бота в режиме "выбор группы/преподавателей/недели/аудитории"
        self.__in_groups = {}  # Список групп и их group_id
        self.__in_teachers = {}  # Список преподавателей и их teacher_id
        self.__in_places = {}  # Список аудиторий и их place_id
        self.__in_dates = {}  # Список учебных недель и их date_id
        self.__in_week = {}  # Таблица с расписанием текущей недели
        self.__week_id = ''  # id текущей недели

        soup = ''  # Разобранная страница
        raw_input = ''  # Неразобранная страница
        user_dir = ''  # Переменная для пути к каталогу пользователей
        menu_1 = {}  # Переменная для хранения главного меню
        key_list_groups = {}  # Переменная для хранения списка групп
        user_config = {}  # Переменная для хранения данных конфига пользователя

        # Смотрим под чем исполняется скрипт, и указываем правильные пути
        if os.name == 'nt':
            user_dir = os.path.join(os.getcwd(), 'users\\')
        else:
            user_dir = os.path.join(os.getcwd(), 'users/')

        timing = time.time()  # Инициализируем таймер
        in_rasp_time = {}
        in_rasp_time_vih = {}
        key_list_0 = ''
        log_dt = ''

    def load_main_data(self):
        """Парсит списки групп, преподавателей, аудиторий и недель."""
        try:
            raw_input = requests.post('https://sarfti.ru/?page_id=20', data={'page_id': '20', 'view': 'Просмотр'}).text
            # разбираем страницу
            soup = BeautifulSoup(raw_input, 'lxml')
            # во временные переменные загоняем данные из таблиц <td></td> с указанными тегами
            groups = [i.findAll('option') for i in soup.findAll('select', attrs={'name': 'group_id'})]
            teachers = [i.findAll('option') for i in soup.findAll('select', attrs={'name': 'teacher_id'})]
            places = [i.findAll('option') for i in soup.findAll('select', attrs={'name': 'place_id'})]
            dates = [i.findAll('option') for i in soup.findAll('select', attrs={'name': 'date_id'})]

            # парсится время пар
            for item in soup.findAll('table', attrs={'style': 'width: 274px; border-style: none;'}):
                in_rasp_time = dict(x.split('=') for x in item.text.replace('\n\n\n1 пара', '1 пара').
                                    replace('\xa0', ' ').replace('\n\n\n', ';').
                                    replace('\n–\n', '=').replace('\n', ' | ')[:-1].split(';'))
                break
            for item in soup.findAll('table', attrs={'style': 'width: 273px; border: none;'}):
                in_rasp_time_vih = dict(x.split('=') for x in
                                        item.text.replace('\n\n\n1 пара', '1 пара').
                                        replace('\xa0', ' ').replace('\n\n\n', ';').
                                        replace('\n–\n', '=').replace('\n', ' | ')[:-1].split(';'))
                break

            # прогоняем цикл по всем переменным выше, заполняя списки
            for item in [groups, teachers, places, dates]:
                # прогоняем цикл по всем элементам
                for i in range(0, item[0].__len__()):
                    # если элемент не содержит "Выберите", то загоняем его в список
                    if 'Выберите' not in item[0][i].text:
                        # если разбираем элементы из временной переменной groups
                        if item == groups:
                            self.__in_groups[item[0][i].attrs['value']] = item[0][i].text
                        # если разбираем элементы из временной переменной teachers
                        if item == teachers:
                            self.__in_teachers[item[0][i].attrs['value']] = item[0][i].text
                        # если разбираем элементы из временной переменной places
                        if item == places:
                            self.__in_places[item[0][i].attrs['value']] = item[0][i].text
                        # если разбираем элементы из временной переменной dates
                        if item == dates:
                            self.__in_dates[item[0][i].attrs['value']] = item[0][i].text
                        # условия выше загнаны в один цикл, для экономии ресурсов

            # удаляем временные переменные из памяти, они нам больше не нужны
            # del groups, teachers, places, dates, i, item
        except Exception as e:
            print(e)
            pass


    def _cal_current_week(self):
        """Вычисляет текущую неделю"""
        # определяем рабочую неделю
        now = datetime.now()
        for week in list(self.__in_dates):
            if (pd.to_datetime(self.__in_dates[week]) - timedelta(days=1) <= now <
                    pd.to_datetime(self.__in_dates[week]) + timedelta(days=7)):
                # current_week = pd.to_datetime(in_dates[week]).strftime('%Y-%m-%d')
                self.__week_id = week
                break



    def _get_week_chedule(self, week_id):
        try:
            # методом HTTP.POST забираем нужную страницу с сайта
            answer = requests.post('http://scs.sarfti.ru/login/index',
                                   data={'login': '', 'password': '', 'guest': 'Войти+как+Гость'})

            traw_input = requests.post('http://scs.sarfti.ru/date/printT',
                                       data={'id': week_id, 'show': 'Распечатать', 'list': 'list',
                                             'compact': 'compact'},
                                       cookies=answer.history[0].cookies)
            traw_input.encoding = 'utf-8'

            # разбираем страницу
            pd_temp = pd
            for item in pd_temp.read_html(StringIO(traw_input.text)):
                if 'День' and 'Пара' in item:
                    try:
                        os.remove('in_week.h5')
                    except Exception as e:
                        print(e)
                        pass
                    store = pd.HDFStore('in_week.h5')
                    store[week_id] = item
                    # store[""] = item
                    store.close()
                    self.__in_week = item
                    break

        except Exception as e:
            print(e)
            pass



    def get_week(self):
        return self.__week_id


if __name__ == "__main__":
    schedule = ScheduleData()
    schedule.load_main_data()
    schedule._cal_current_week()
    schedule._get_week_chedule(schedule.get_week())