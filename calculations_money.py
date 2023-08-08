import math
import pandas as pd

def clear_calculations(session, df):
    by_x = math.floor(df['Значение'][3] / float(session['second_form']['width']))
    by_y = math.floor(df['Значение'][2] / float(session['second_form']['length']))
    number_multi = int(by_x * by_y)
    number_items = int(session['second_form']['length_num']) * int(session['second_form']['width_num'])
    number_smallitems = int(number_items * number_multi)
    if int(session['home_form']['field3']) < number_smallitems:
        number_smallitems = int(session['home_form']['field3'])
        number_multi = number_smallitems / number_items
    return [number_multi, number_items, number_smallitems]

def sep_calculations(session, df):
    by_x = float(session['second_form']['width']) * (int(session['second_form']['length_num']) + 1) 
    by_y = float(session['second_form']['length']) * (int(session['second_form']['width_num']) + 1) 
    number_items = int(session['second_form']['length_num']) * int(session['second_form']['width_num'])
    number_multi = int(session['home_form']['field3']) /  number_items
    time_scrub = math.ceil((by_x + by_y) / df['Значение'][0] * df['Значение'][3] / number_items)
    time_jump = df['Значение'][1] * df['Значение'][4]
    time_sar = math.ceil((by_x + by_y) / df['Значение'][2] * df['Значение'][5] / number_items)
    time = [time_scrub, time_jump, time_sar, number_multi, number_items]
    return time
    
def create_export(session):
    SMD = [
        session['SMD_form']['time_pc'],
        session['SMD_form']['time_all'],
        session['SMD_form']['money_pc'],
        session['SMD_form']['money_all']
        ]
    SMD_re = [
        session['SMD_form']['time_re_pc'],
        session['SMD_form']['time_re_all'],
        session['SMD_form']['money_re_pc'],
        session['SMD_form']['money_re_all']
        ]
    THT = [
        session['THT_form']['time_pc'],
        session['THT_form']['time_all'],
        session['THT_form']['money_pc'],
        session['THT_form']['money_all']
        ]
    THT_re = [
        session['THT_form']['time_re_pc'],
        session['THT_form']['time_re_all'],
        session['THT_form']['money_re_pc'],
        session['THT_form']['money_re_all']
        ]
    Wave = [
        session['Wave_form']['time_pc'],
        session['Wave_form']['time_all'],
        session['Wave_form']['money_pc'],
        session['Wave_form']['money_all']
        ]
    Wave_re = [
        session['Wave_form']['time_re_pc'],
        session['Wave_form']['time_re_all'],
        session['Wave_form']['money_re_pc'],
        session['Wave_form']['money_re_all']
        ]
    HRL = [
        session['HRL_form']['time_pc'],
        session['HRL_form']['time_all'],
        session['HRL_form']['money_pc'],
        session['HRL_form']['money_all']
        ]
    HRL_re = [
        session['HRL_form']['time_re_pc'],
        session['HRL_form']['time_re_all'],
        session['HRL_form']['money_re_pc'],
        session['HRL_form']['money_re_all']
        ]
    Hand = [
        session['Hand_form']['time_pc'],
        session['Hand_form']['time_all'],
        session['Hand_form']['money_pc'],
        session['Hand_form']['money_all']
        ]
    Test = [
        session['Test_form']['time_pc'],
        session['Test_form']['time_all'],
        session['Test_form']['money_pc'],
        session['Test_form']['money_all']
        ]
    Clear = [
        session['Clear_form']['time_pc'],
        session['Clear_form']['time_all'],
        session['Clear_form']['money_pc'],
        session['Clear_form']['money_all']
        ]
    Handv = [
        session['Handv_form']['time_pc'],
        session['Handv_form']['time_all'],
        session['Handv_form']['money_pc'],
        session['Handv_form']['money_all']
        ]
    Sep = [
        session['Sep_form']['time_pc'],
        session['Sep_form']['time_all'],
        session['Sep_form']['money_pc'],
        session['Sep_form']['money_all']
        ]
    Xray = [
        session['Xray_form']['time_pc'],
        session['Xray_form']['time_all'],
        session['Xray_form']['money_pc'],
        session['Xray_form']['money_all']
        ]
    Add = [
        session['Add_form']['time_pc'],
        session['Add_form']['time_all'],
        session['Add_form']['money_pc'],
        session['Add_form']['money_all']
        ]
    data = [SMD, SMD_re, THT, THT_re, Wave, Wave_re, HRL, HRL_re, Hand, Test, Clear, Handv, Sep, Xray, Add]
    headers = ["Время на 1 ПУ", "Время на партию", "Стоимость 1 ПУ", "Стоимость на партию"]
    row_headers = [
        "Автоматический поверхностный монтаж SMT",
        "Автоматический поверхностный монтаж SMT, переналадка", 
        "Селективная пайка THT",
        "Селективная пайка THT, переналадка",
        "Волновая пайка",
        "Волновая пайка, переналадка",
        "Селективная лакировка HRL",
        "Селективная лакировка HRL, переналадка",
        "Ручной монтаж",
        "Тестирование",
        "Отмывка",
        "Ручная лакировка",
        "Разделение",
        "Рентгенконтроль",
        "Доп. работы"
        ]
    df = pd.DataFrame(data, columns=headers, index=row_headers)
    df = df.drop(df[(df == "-").all(axis=1)].index)
    
    headers2 = ["","Стоимость"]
    row_headers2 = [
        "Трафареты"
        "Проверка документации"
        "Создание ЕВОМ"
    ]
    data2 = prepare(session)
    df2 = pd.DataFrame(data2, columns=headers2)
    return [df, df2]

def prepare(session):
    df = pd.read_csv('data/Traf.csv')
    df2 = pd.read_csv('data/tarifs.csv')
    if "Trafs_costs_select" in session["second_form"]:
        if session["second_form"]["Trafs_costs_select"] == "1": 
            if session["second_form"]["Traf_value2"] == "1":
                traf = int(df['Значение'][0])
            if session["second_form"]["Traf_value2"] == "2":
                traf = int(df['Значение'][1])
            if session["second_form"]["Traf_value2"] == "3":
                traf = int(df['Значение'][2])
            traf *= int(session["second_form"]["Traf_value2"])
        elif session["second_form"]["Trafs_costs_select"] == "2":
            traf = int(session["second_form"]["Traf_value"])
    doc = df2["Стоимость, руб/ч"][23]
    ebom = df2["Стоимость, руб/ч"][23] * session["tables"][4]
    return [["Трафареты", traf], ["Проверка документации", doc], ["Создание EBOM", ebom]]
    
