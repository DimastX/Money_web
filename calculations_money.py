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
    time_sar = math.ceil((by_x + by_y) / df['Значение'][2]  / number_items)
    time = [time_scrub, time_jump, time_sar, number_multi, number_items]
    return time
    
def create_export(session):
    batch = int(session['home_form']['field3'])
    SMD_re_t = [
        session['SMD_form']['time_re_pc_t'],
        session['SMD_form']['time_re_all_t'],
        session['SMD_form']['money_re_pc_t'],
        session['SMD_form']['money_re_all_t']
        ]
    SMD_t = [
        session['SMD_form']['time_pc_t'],
        session['SMD_form']['time_all_t'],
        session['SMD_form']['money_pc_t'],
        session['SMD_form']['money_all_t']
        ]    
    SMD_re_b = [
        session['SMD_form']['time_re_pc_b'],
        session['SMD_form']['time_re_all_b'],
        session['SMD_form']['money_re_pc_b'],
        session['SMD_form']['money_re_all_b']
        ]
    SMD_b = [
        session['SMD_form']['time_pc_b'],
        session['SMD_form']['time_all_b'],
        session['SMD_form']['money_pc_b'],
        session['SMD_form']['money_all_b']
        ]
    if session['SMD_form']['repair_time_all'] != '-':
        SMD_rep =[
            str(math.ceil(int(str(session['SMD_form']['repair_time_all']).split(" ")[0]) / batch * 3600)) + " с",
            session['SMD_form']['repair_time_all'],
            str(math.ceil(int(str(session['SMD_form']['repair_money_all']).split(" ")[0]) / batch)) + " руб",
            session['SMD_form']['repair_money_all']
        ]
        SMD_cont =[
            str(math.ceil(int(str(session['SMD_form']['control_time_all']).split(" ")[0]) / batch * 3600)) + " с",
            session['SMD_form']['control_time_all'],
            str(math.ceil(int(str(session['SMD_form']['control_money_all']).split(" ")[0]) / batch)) + " руб",
            session['SMD_form']['control_money_all']
        ]
    else:
        SMD_rep =[
            "-",
            "-",
            "-",
            "-"
        ]
        SMD_cont =[
            "-",
            "-",
            "-",
            "-"
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
    if session['Wave_form']['repair_time_all'] != '-':
        Wave_rep =[
            str(math.ceil(int(str(session['Wave_form']['repair_time_all']).split(" ")[0]) / batch * 3600)) + " с",
            session['Wave_form']['repair_time_all'],
            str(math.ceil(int(str(session['Wave_form']['repair_money_all']).split(" ")[0]) / batch)) + " руб",
            session['Wave_form']['repair_money_all']
        ]
        Wave_cont =[
            str(math.ceil(int(str(session['Wave_form']['control_time_all']).split(" ")[0]) / batch * 3600)) + " с",
            session['Wave_form']['control_time_all'],
            str(math.ceil(int(str(session['Wave_form']['control_money_all']).split(" ")[0]) / batch)) + " руб",
            session['Wave_form']['control_money_all']
        ]
    else:
        Wave_rep =[
            "-",
            "-",
            "-",
            "-"
        ]
        Wave_cont =[
            "-",
            "-",
            "-",
            "-"
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
    HRL_rep = data_creation(session['HRL_form']['repair_time_all'], session['HRL_form']['repair_money_all'], batch)
    HRL_cont = data_creation(session['HRL_form']['control_time_all'], session['HRL_form']['control_money_all'], batch)
    Hand = [
        session['Hand_form']['time_pc'],
        session['Hand_form']['time_all'],
        session['Hand_form']['money_pc'],
        session['Hand_form']['money_all']
        ]
    Hand_cont = data_creation(session['Hand_form']['control_time_all'], session['Hand_form']['control_money_all'], batch)
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
    Clear_cont = data_creation(session['Clear_form']['control_time_all'], session['Clear_form']['control_money_all'], batch)
    Handv = [
        session['Handv_form']['time_pc'],
        session['Handv_form']['time_all'],
        session['Handv_form']['money_pc'],
        session['Handv_form']['money_all']
        ]
    Handv_cont = data_creation(session['Handv_form']['control_time_all'], session['Handv_form']['control_money_all'], batch)
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
    data = [ SMD_re_t, SMD_t, SMD_re_b, SMD_b, SMD_rep, SMD_cont ,THT_re, THT, Wave_re, Wave, Wave_rep, Wave_cont, HRL_re, HRL, HRL_rep, HRL_cont, Hand, Handv_cont, 
            Hand_cont, Test, Clear, Clear_cont, Handv, Sep, Xray, Add]
    headers = ["Время на 1 ПУ", "Время на партию", "Стоимость 1 ПУ", "Стоимость на партию"]
    row_headers = [
        "Автоматический поверхностный монтаж SMT Pri, переналадка",
        "Автоматический поверхностный монтаж SMT Pri", 
        "Автоматический поверхностный монтаж SMT Sec, переналадка",
        "Автоматический поверхностный монтаж SMT Sec", 
        "Ремонт на поверхностном монтаже",
        "Контроль на поверхностном монтаже",
        "Селективная пайка THT, переналадка",
        "Селективная пайка THT",
        "Волновая пайка, переналадка",
        "Волновая пайка",
        "Ремонт на волновой пайке",
        "Контроль на волновой пайке",
        "Селективная лакировка HRL, переналадка",
        "Селективная лакировка HRL", 
        "Ремонт на селективной лакировке",
        "Контроль на селективной лакировке",
        "Ручной монтаж",
        "Контроль ручного монтажа",
        "Тестирование",
        "Отмывка",
        "Контроль после отмывки",
        "Ручная лакировка",
        "Контроль ручной лакировки",
        "Разделение",
        "Рентгенконтроль",
        "Доп. работы"
        ]
    df = pd.DataFrame(data, columns=headers, index=row_headers)
    df = df.drop(df[(df == "-").all(axis=1)].index)
    sum_time_pc, sum_money_pc, sum_time_all, sum_money_all = 0, 0, 0, 0
    for i in range(df.shape[0]):
        sum_time_pc += int(str(df.iloc[i, 0]).split(" ")[0])
        sum_time_all += int(str(df.iloc[i, 1]).split(" ")[0])
        sum_money_pc += int(str(df.iloc[i, 2]).split(" ")[0])
        sum_money_all += int(str(df.iloc[i, 3]).split(" ")[0])
    total = [str(sum_time_pc) + " с", str(sum_time_all) + " ч", str(sum_money_pc) + " руб", str(sum_money_all) + " руб"]
    df.loc["Итого"] = total
    if 'prepare' in session['second_form']:
        headers2 = ["","Стоимость"]
        data2 = prepare(session)
        prep_sum = 0
        for data_in_data2 in data2:
            prep_sum += int(str(data_in_data2[1]).split(" ")[0])
        data2.append(["Итого", str(prep_sum) + " руб" ])
        prep_sum_pc = int(prep_sum / batch)
        df.loc["Итого с подготовкой производства"] = [str(sum_time_pc) + " с", str(sum_time_all) + " ч", str(sum_money_pc + prep_sum_pc) + " руб", str(sum_money_all + prep_sum) + " руб"]
        df2 = pd.DataFrame(data2, columns=headers2)
        return [df, df2]
    return [df, 1]

def prepare(session):
    df = pd.read_csv('data/Traf.csv')
    df2 = pd.read_csv('data/tarifs.csv')
    if "Trafs_costs_select" in session["second_form"] and "Traf" in session["second_form"]:
        if session['second_form']['Traf'] == "2":
            if session["second_form"]["Trafs_costs_select"] == "1": 
                if session["second_form"]["Traf_value2"] == "1":
                    traf = int(df['Значение'][0])
                if session["second_form"]["Traf_value2"] == "2":
                    traf = int(df['Значение'][1])
                if session["second_form"]["Traf_value2"] == "3":
                    traf = int(df['Значение'][2])
            elif session["second_form"]["Trafs_costs_select"] == "2":
                traf = int(session["second_form"]["Traf_value"])
            traf *= int(session["second_form"]["sides_SMD"])
    else:
        traf = 0
    traf = str(traf) + " руб"
    doc = str(df2["Стоимость, руб/ч"][23]) + " руб"
    ebom = str(df2["Стоимость, руб/ч"][24] * session["tables"][4]) + " руб"
    return [["Трафареты", traf], ["Проверка документации", doc], ["Создание EBOM", ebom]]
    
def data_creation(time_all, money_all, batch):
    if time_all == "-":
        list1 = [
            "-",
            "-",
            "-",
            "-"
        ]
    else:
        list1 = [
            str(math.ceil(int(str(time_all).split(" ")[0]) / batch * 3600)) + " с",
            time_all,
            str(math.ceil(int(str(money_all).split(" ")[0]) / batch)) + " руб",
            money_all
        ]
    return list1