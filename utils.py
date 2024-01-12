

async def find_coincidence_in_list(mes_text, roster, prefix=""):
    """Находит совпадения сообщения в списке roster"""
    result_roster = {}
    for roster_key in roster:
        if roster[roster_key].lower().startswith(mes_text.lower()) is True:
            result_roster[roster_key + prefix] = roster[roster_key]
    return result_roster


async def find_coincidence_group_teacher(mes_text, schedule):
    """Находит совпадение сообщения с группами и ФИО преподавателей"""
    all_coincidence = [await find_coincidence_in_list(mes_text, schedule.get_groups(), 'g'),
                       await find_coincidence_in_list(mes_text, schedule.get_teachers(), 't')]
    return all_coincidence
