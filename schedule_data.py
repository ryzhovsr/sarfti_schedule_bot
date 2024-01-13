import contextlib
import os
import pickle
import time
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
# требуется наличие библиотеки lxml


class ScheduleData:
    def __init__(self):
        self.__groups = {}      # Группы
        self.__teachers = {}    # Преподаватели
        self.__places = {}      # Аудитории
        self.__dates = {}       # Учебные недели

        self.__current_week_id = ''            # id текущей (рабочей) недели
        self.__week_ids = []                   # id всех доступные недель
        self.__schedule_current_week = {}      # Расписание текущей (рабочей) недели
        self.__schedule_week_dir = ''          # Путь к директории для файла с расписанием
        self.__schedule_week_file_name = 'schedule_week'

        self.__class_time_weekdays = {}  # Время учебных занятий в будни (понедельник – пятница)
        self.__class_time_saturday = {}  # Время учебных занятий в субботу

        self.__html_data_sarfti_schedule = ''  # Страница расписания СарФТИ c исходным html кодом
        self.__html_soup_sarfti_schedule = ''  # Разобранная html страница расписания СарФТИ

        self.schedule_management_html = None  # Страница для использования хэш данных

        # Смотрим под чем исполняется скрипт, и указываем правильный путь
        if os.name == 'nt':
            self.__schedule_week_dir = os.path.join(os.getcwd(), 'Data\\')
        else:
            self.__schedule_week_dir = os.path.join(os.getcwd(), 'Data/')

        self.update_schedule()

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
        """Парсит расписание по заданному id недели"""
        # Данные сайта по печати (вывода) расписания на текущую неделю
        current_week_schedule_html = requests.post('http://scs.sarfti.ru/date/printT',
                                                   data={'id': week_id, 'show': 'Распечатать',
                                                         'list': 'list', 'compact': 'compact'},
                                                   cookies=self.schedule_management_html.history[0].cookies)

        current_week_schedule_html.encoding = 'utf-8'

        for item in pd.read_html(StringIO(current_week_schedule_html.text)):
            if 'День' and 'Пара' in item:
                with open(self.__schedule_week_dir + self.__schedule_week_file_name + '_' + week_id + '.pkl', "wb") as file:
                    pickle.dump(item, file)
                self.__schedule_current_week = item
                break

    def update_schedule(self):
        """Обновляет расписание"""
        self.__load_main_data()
        self.__cal_current_week()
        self.__load_schedule()

    def __del_store(self):
        """Удаление всех старых файлов с расписанием"""
        with contextlib.suppress(Exception):
            for filename in os.listdir(self.__schedule_week_dir):
                file_path = os.path.join(self.__schedule_week_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

    def __load_schedule(self):
        """Загружает в файлы расписание для актуальной и более новых недель"""
        self.__del_store()
        # Данные сайта по управлению расписанием
        self.schedule_management_html = requests.post('http://scs.sarfti.ru/login/index',
                                                      data={'login': '', 'password': '',
                                                            'guest': 'Войти+как+Гость'})
        for week in self.__week_ids:
            self.__parse_schedule_week(week)
        self.schedule_management_html = None

    # TO DO реализовать возможность отсрочить плановый парсинг, ради исключения случайного за-None-вания кэша
    def run_updates(self, iterations_between_updates=30, sleep_time=120):
        """Запускает обновление основных данных и парсер расписания
        iterations_between_updates=30 и sleep_time=120 - будет обновляться база каждый день, а расписание каждые 2 мин
        """
        while True:
            self.__load_main_data()
            time.sleep(sleep_time)
            # Данные сайта по управлению расписанием
            self.schedule_management_html = requests.post('http://scs.sarfti.ru/login/index',
                                                          data={'login': '', 'password': '',
                                                                'guest': 'Войти+как+Гость'})
            for i in range(iterations_between_updates):
                self.__parse_schedule_week(self.__load_schedule())
                time.sleep(sleep_time)
            self.schedule_management_html = None

    def __get_week_schedule_all(self, week_num):
        """Возвращает расписание на неделю по week_num, где 0 - текущая, 1 - следующ. ..."""
        week = str(int(self.__current_week_id) + week_num)
        with open(self.__schedule_week_dir + self.__schedule_week_file_name + '_' + week + '.pkl', "rb") as file:
            loaded_table = pickle.load(file)
        return loaded_table

    def get_week_schedule(self, output_type, target, week_num):
        """Возвращает расписание в зависимости от типа расписания и по чему выводить (например, название группы)"""
        loaded_table = self.__get_week_schedule_all(week_num)
        # print(loaded_table)
        week_id = str(int(self.__current_week_id) + week_num)
        text_out = '*📅 ' + pd.to_datetime(self.__dates[week_id]).strftime('%d %B') + ' - ' + \
                   (pd.to_datetime(self.__dates[week_id]) + timedelta(days=7)).strftime('%d %B %Yг') + '*\n'

        dayf = False
        dayprev = ''
        for index, row in loaded_table.query(output_type + ' == @target').iterrows():
            dayt = str(row['День'])
            if dayprev == dayt and dayf == False: dayf = True
            if dayprev != dayt:
                dayprev = dayt
                dayf = False
                text_out = text_out + '\n'

            if dayt == 'ПН' and dayf == False:
                text_out = text_out + '🔹 *ПОНЕДЕЛЬНИК:*\n'
            if dayt == 'ВТ' and dayf == False:
                text_out = text_out + '🔹 *ВТОРНИК:*\n'
            if dayt == 'СР' and dayf == False:
                text_out = text_out + '🔹 *СРЕДА:*\n'
            if dayt == 'ЧТ' and dayf == False:
                text_out = text_out + '🔹 *ЧЕТВЕРГ:*\n'
            if dayt == 'ПТ' and dayf == False:
                text_out = text_out + '🔹 *ПЯТНИЦА:*\n'
            if dayt == 'СУБ' and dayf == False:
                text_out = text_out + '🔹 *СУББОТА:*\n'
            if dayt == 'ВС' and dayf == False:
                text_out = text_out + '🔹 *ВОСКРЕСЕНЬЕ:*\n'

            tnum = str(row['Пара'])
            if str(row['Пара']) == '1': tnum = u'\u0031\ufe0f\u20e3'
            if str(row['Пара']) == '2': tnum = u'\u0032\ufe0f\u20e3'
            if str(row['Пара']) == '3': tnum = u'\u0033\ufe0f\u20e3'
            if str(row['Пара']) == '4': tnum = u'\u0034\ufe0f\u20e3'
            if str(row['Пара']) == '5': tnum = u'\u0035\ufe0f\u20e3'
            if str(row['Пара']) == '6': tnum = u'\u0036\ufe0f\u20e3'
            if str(row['Пара']) == '7': tnum = u'\u0037\ufe0f\u20e3'
            if str(row['Пара']) == '8': tnum = u'\u0038\ufe0f\u20e3'
            if str(row['Пара']) == '9': tnum = u'\u0039\ufe0f\u20e3'

            ttype = str(row['Тип']) + ','
            if str(row['Тип']) == 'Лекция': ttype = u'💬'
            if str(row['Тип']) == 'Практика': ttype = u'🔥'
            if 'Лаб' in str(row['Тип']): ttype = str(row['Тип']).replace('Лаб раб', u'🔥').replace('Лаб', u'🔥').replace(
                '1 пг', u'🅰').replace('2 пг', u'🅱')

            if output_type == 'Аудитория':
                text_out = (text_out + \
                           tnum + ' ' + \
                           str(row['Преподаватель']) + ', ' + \
                           str(row['Группа']) + '\n')
                           # ttype + ', ' + \
                           # str(row['Предмет']))

            else:
                tplace = str(row['Аудитория'])
                if 'ОНЛАЙН' in str(row['Аудитория']): tplace = str(row['Аудитория']).replace('ОНЛАЙН', u' 📡')
                if 'Онлайн 1ДО' in str(row['Аудитория']): tplace = str(row['Аудитория']).replace('Онлайн 1ДО', u'1ДО 📡')
                if 'Онлайн 2ДО' in str(row['Аудитория']): tplace = str(row['Аудитория']).replace('Онлайн 1ДО', u'2ДО 📡')

                text_out = text_out + \
                           tnum + ' ' + ttype + ' ' + \
                           '[' + tplace + '] ' + \
                           str(row['Предмет']) + ', '

                if output_type == 'Группа':
                    text_out = text_out + str(row['Преподаватель']) + '\n'
                elif output_type == 'Преподаватель':
                    text_out = text_out + str(row['Группа']) + '\n'

        return text_out

    def get_week_schedule_group(self, group_name, week_num=0):
        """Возвращает расписание группы с именем group_name"""
        return self.get_week_schedule('Группа', group_name, week_num)

    def get_week_schedule_teacher(self, teacher_name, week_num=0):
        """Возвращает расписание группы с именем group_name"""
        return self.get_week_schedule('Преподаватель', teacher_name, week_num)

    def get_week_schedule_place(self, place_name, week_num=0):
        """Возвращает расписание группы с именем group_name"""
        return self.get_week_schedule('Аудитория', place_name, week_num)


    def get_dates(self):
        """Возвращает учебные недели"""
        return self.__dates

    def get_groups(self):
        """Возвращает группы"""
        return self.__groups

    def get_teachers(self):
        """Возвращает преподавателей"""
        return self.__teachers

    def get_schedule_week_dir(self):
        """Возвращает путь к директории для файлов с расписанием, а не путь к файлу"""
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
    # schedule.update_schedule()
    # print(schedule.get_week_schedule_group('ЦТ-40', 1))
    # print(schedule.get_week_schedule_teacher('Федоренко Г.А.'))
    print(schedule.get_week_schedule_place('к2,117', 1))

    # schedule.get_week_schedule('Группа', 'АВТ-13')
    # print(schedule.get_week_schedule(0)) # вытаскивание расписание недели
    # print(schedule.get_week_schedule(1))
    # print(schedule.get_week_schedule(2))
    # print(schedule.get_week_schedule(3))
    # print(schedule.get_week_schedule(4))
