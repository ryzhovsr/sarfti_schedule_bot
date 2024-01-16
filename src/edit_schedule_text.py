def get_line_schedule_teacher(num_lesson, place, groups, lesson, lesson_type):
    """Возвращает формализованную строку для преподавателя"""
    return get_num_lesson(num_lesson) + get_emoji(lesson_type) + lesson_type + ' [' + place + '] ' + groups + ' ' + lesson + '\n'


def get_line_schedule_group(num_lesson, place, teacher, lesson, lesson_type):
    """Возвращает формализованную строку для группы"""
    return get_num_lesson(num_lesson) + get_emoji(lesson_type) + lesson_type + ' [' + place + '] ' + lesson + ', ' + teacher + '\n'


def get_num_lesson(num_lesson):
    """Возвращает номер пары в виде эмодзи"""
    return chr(0x0030 + num_lesson) + '\uFE0F' + chr(0x20E3)


def get_full_day_name(user_day):
    """Возвращает полное название дня недели"""
    full_days = ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']
    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СУБ', 'ВС']
    return '\n🔹 *' + full_days[days.index(user_day)] + ':*\n'


def get_emoji(lesson_type):
    if lesson_type == 'Лекция':
        return u'💬'
    if lesson_type == 'Практика':
        return u'📝'
    if lesson_type.startswith('Лаб'):
        if '1' in lesson_type:
            return u'🔬' + u'➊ '
        if '2' in lesson_type:
            return u'🔬' + u'➋ '
        return u'🔬'
    return u'🔥'


def form_schedule_teacher(table, target):
    """Возвращает текст расписания для преподавателя"""
    lesson = table.query(f'Преподаватель == @target').iterrows()
    index, prev_row = next(lesson)
    prev_day = str(prev_row['День'])
    list_groups = prev_row['Группа']

    out_text = get_full_day_name(prev_row['День'])
    repeat = False
    while True:
        try:
            index, row = next(lesson)
            if (row['Пара'] == prev_row['Пара']) and (str(row['День']) == prev_day):
                list_groups = list_groups + ', ' + row['Группа']
                repeat = True
            else:
                if not repeat:
                    list_groups = prev_row['Группа']
                    # repeat = False
                out_text = out_text + get_line_schedule_teacher(prev_row['Пара'],
                                                                prev_row['Аудитория'],
                                                                list_groups,
                                                                prev_row['Предмет'],
                                                                prev_row['Тип'])
                if str(row['День']) != prev_day:
                    t = get_full_day_name(row['День'])
                    out_text = out_text + t

                repeat = False
                list_groups = row['Группа']

            prev_day = str(row['День'])
            prev_row = row
        except StopIteration:
            break
    out_text = out_text + get_line_schedule_teacher(prev_row['Пара'],
                                                    prev_row['Аудитория'],
                                                    list_groups,
                                                    prev_row['Предмет'],
                                                    prev_row['Тип'])
    return out_text


def form_schedule_group(table, target):
    """Возвращает текст расписания для группы"""
    prev_row = ''
    out_text = ''
    for index, row in table.query('Группа == @target').iterrows():
        if prev_row != row['День']:
            out_text = out_text + get_full_day_name(row['День'])
        out_text = out_text + get_line_schedule_group(row['Пара'],
                                                      row['Аудитория'],
                                                      row['Преподаватель'],
                                                      row['Предмет'],
                                                      row['Тип'])
        prev_row = row['День']
    return out_text
