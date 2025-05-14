import math
import pandas as pd

# === Функции для калькуляции производственных затрат ===

# --- Расчёт параметров для операции отмывки ---
def clear_calculations(session, df):
    # Расчет количества мультизаготовок (МЗ), помещающихся по ширине рамки отмывки
    by_x = math.floor(df['Значение'][3] / float(session['second_form']['width']))  #Ширина рамки отмывки/ширину мз 
    # Расчет количества мультизаготовок (МЗ), помещающихся по длине рамки отмывки
    by_y = math.floor(df['Значение'][2] / float(session['second_form']['length']))
    # Общее количество МЗ в рамке
    number_multi = int(by_x * by_y) #Количество мультизаготовок, помещающихся в рамке отмывки одновременно
    # Количество плат в одной МЗ
    number_items = int(session['second_form']['length_num']) * int(session['second_form']['width_num']) #Количество плат в мз
    # Общее количество плат в рамке отмывки
    number_smallitems = int(number_items * number_multi) #Количество плат в рамке отмывки одновременно
    
    # Корректировка, если размер партии меньше, чем вместимость рамки
    if int(session['home_form']['field3']) < number_smallitems: #Если размер партии меньше, чем количество плат в отмывке одновременно
        number_smallitems = int(session['home_form']['field3'])
        number_multi = number_smallitems / number_items # Пересчитываем количество МЗ исходя из размера партии
    return [number_multi, number_items, number_smallitems] #Количество мз в рамке отмывки, количество плат в мз, количество плат в рамке отмывки


# --- Расчёт времени на операцию разделения мультизаготовок ---
def sep_calculations(session, df):
    # Расстояние, проходимое инструментом по оси X для одной МЗ
    by_x = float(session['second_form']['width']) * (int(session['second_form']['length_num']) + 1) #ширина мз * (количество плат в длину + 1) = расстояние пройденное по х
    # Расстояние, проходимое инструментом по оси Y для одной МЗ
    by_y = float(session['second_form']['length']) * (int(session['second_form']['width_num']) + 1) 
    # Количество плат в одной МЗ
    number_items = int(session['second_form']['length_num']) * int(session['second_form']['width_num']) #Количество пп в мз
    # Общее количество МЗ в партии
    number_multi = int(session['home_form']['field3']) /  number_items #Количество мз
    # Время скрайбирования на одну плату
    time_scrub = math.ceil((by_x + by_y) / df['Значение'][0] * df['Значение'][3] / number_items) #(Расстояние / скорость скрайбирования) * поправочный коэф-т / количество пп в мз
    # Время на перемычки (учитывается как константа)
    time_jump = df['Значение'][1] * df['Значение'][4] #
    # Время SAR на одну плату
    time_sar = math.ceil((by_x + by_y) / df['Значение'][2]  * df['Значение'][5]/ number_items) #(Расстояние / скорость SAR) * поправочный коэф-т / количество пп в мз
    time = [time_scrub, time_jump, time_sar, number_multi, number_items]
    return time
    

# --- Вспомогательная функция: преобразование строки с числом и единицей измерения в целое число ---
# Пример: "100 руб" -> 100
def strtoint(string):
    if string != "-": # Проверка на пустое значение (обозначенное как "-")
        return int(string.split(" ")[0]) # Берем первую часть строки до пробела и преобразуем в int
    return "-" # Возвращаем "-", если исходная строка была такой

"""Создание итоговой таблицы"""
def create_export(session):
    batch = int(session['home_form']['field3'])
    #Создание массивов для каждой строки затрат
    SMD_re_t = [
        strtoint(session['SMD_form']['time_re_pc_t']),
        strtoint(session['SMD_form']['time_re_all_t']),
        strtoint(session['SMD_form']['money_re_pc_t']),
        strtoint(session['SMD_form']['money_re_all_t'])
        ]
    SMD_t = [
        strtoint(session['SMD_form']['time_pc_t']),
        strtoint(session['SMD_form']['time_all_t']),
        strtoint(session['SMD_form']['money_pc_t']),
        strtoint(session['SMD_form']['money_all_t'])
        ]    
    SMD_re_b = [
        strtoint(session['SMD_form']['time_re_pc_b']),
        strtoint(session['SMD_form']['time_re_all_b']),
        strtoint(session['SMD_form']['money_re_pc_b']),
        strtoint(session['SMD_form']['money_re_all_b'])
        ]
    SMD_b = [
        strtoint(session['SMD_form']['time_pc_b']),
        strtoint(session['SMD_form']['time_all_b']),
        strtoint(session['SMD_form']['money_pc_b']),
        strtoint(session['SMD_form']['money_all_b'])
        ]
    if session['SMD_form']['repair_time_all'] != '-': #В случае если ремонт требуется расчёт значений для ремонта
        SMD_rep =[
            math.ceil(int(str(session['SMD_form']['repair_time_all']).split(" ")[0]) / batch * 3600),
            strtoint(session['SMD_form']['repair_time_all']),
            math.ceil(int(str(session['SMD_form']['repair_money_all']).split(" ")[0]) / batch),
            strtoint(session['SMD_form']['repair_money_all'])
        ]
        SMD_cont =[
            math.ceil(int(str(session['SMD_form']['control_time_all']).split(" ")[0]) / batch * 3600),
            strtoint(session['SMD_form']['control_time_all']),
            math.ceil(int(str(session['SMD_form']['control_money_all']).split(" ")[0]) / batch),
            strtoint(session['SMD_form']['control_money_all'])
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
    THT_pri = [
        strtoint(session['THT_form']['time_pc']),
        strtoint(session['THT_form']['time_all']),
        strtoint(session['THT_form']['money_pc']),
        strtoint(session['THT_form']['money_all'])
        ]
    THT_pri_re = [
        strtoint(session['THT_form']['time_re_pc']),
        strtoint(session['THT_form']['time_re_all']),
        strtoint(session['THT_form']['money_re_pc']),
        strtoint(session['THT_form']['money_re_all'])
        ]
    THT_pri_p =[
        strtoint(session['THT_form']['time_pc_p']),
        strtoint(session['THT_form']['time_all_p']),
        strtoint(session['THT_form']['money_pc_p']),
        strtoint(session['THT_form']['money_all_p'])
    ]    
    THT_sec = [
        strtoint(session['THT_form']['time_pc2']),
        strtoint(session['THT_form']['time_all2']),
        strtoint(session['THT_form']['money_pc2']),
        strtoint(session['THT_form']['money_all2'])
        ]
    THT_sec_re = [
        strtoint(session['THT_form']['time_re_pc2']),
        strtoint(session['THT_form']['time_re_all2']),
        strtoint(session['THT_form']['money_re_pc2']),
        strtoint(session['THT_form']['money_re_all2'])
        ] 
    THT_sec_p = [
        strtoint(session['THT_form']['time_pc2_p']),
        strtoint(session['THT_form']['time_all2_p']),
        strtoint(session['THT_form']['money_pc2_p']),
        strtoint(session['THT_form']['money_all2_p'])
        ]
    THT_rep = data_creation(session['THT_form']['repair_time_all'], session['THT_form']['repair_money_all'], batch)
    THT_cont = data_creation(session['THT_form']['control_time_all'], session['THT_form']['control_money_all'], batch)
    Wave = [
        strtoint(session['Wave_form']['time_pc']),
        strtoint(session['Wave_form']['time_all']),
        strtoint(session['Wave_form']['money_pc']),
        strtoint(session['Wave_form']['money_all'])
        ]
    Wave_p = [
        strtoint(session['Wave_form']['time_pc_p']),
        strtoint(session['Wave_form']['time_all_p']),
        strtoint(session['Wave_form']['money_pc_p']),
        strtoint(session['Wave_form']['money_all_p'])
        ]
    if session['Wave_form']['repair_time_all'] != '-':
        Wave_rep =[
            math.ceil(int(str(session['Wave_form']['repair_time_all']).split(" ")[0]) / batch * 3600),
            strtoint(session['Wave_form']['repair_time_all']),
            math.ceil(int(str(session['Wave_form']['repair_money_all']).split(" ")[0]) / batch),
            strtoint(session['Wave_form']['repair_money_all'])
        ]
        Wave_cont =[
            math.ceil(int(str(session['Wave_form']['control_time_all']).split(" ")[0]) / batch * 3600),
            strtoint(session['Wave_form']['control_time_all']),
            math.ceil(int(str(session['Wave_form']['control_money_all']).split(" ")[0]) / batch),
            strtoint(session['Wave_form']['control_money_all'])
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
        strtoint(session['HRL_form']['time_pc']),
        strtoint(session['HRL_form']['time_all']),
        strtoint(session['HRL_form']['money_pc']),
        strtoint(session['HRL_form']['money_all'])
        ]
    HRL_re = [
        strtoint(session['HRL_form']['time_re_pc']),
        strtoint(session['HRL_form']['time_re_all']),
        strtoint(session['HRL_form']['money_re_pc']),
        strtoint(session['HRL_form']['money_re_all'])
        ]
    HRL_rep = data_creation(session['HRL_form']['repair_time_all'], session['HRL_form']['repair_money_all'], batch)
    HRL_cont = data_creation(session['HRL_form']['control_time_all'], session['HRL_form']['control_money_all'], batch)
    Hand = [
        strtoint(session['Hand_form']['time_pc']),
        strtoint(session['Hand_form']['time_all']),
        strtoint(session['Hand_form']['money_pc']),
        strtoint(session['Hand_form']['money_all'])
        ]
    Hand_cont = data_creation(session['Hand_form']['control_time_all'], session['Hand_form']['control_money_all'], batch)
    Test = [
        strtoint(session['Test_form']['time_pc']),
        strtoint(session['Test_form']['time_all']),
        strtoint(session['Test_form']['money_pc']),
        strtoint(session['Test_form']['money_all'])
        ]
    Clear = [
        strtoint(session['Clear_form']['time_pc']),
        strtoint(session['Clear_form']['time_all']),
        strtoint(session['Clear_form']['money_pc']),
        strtoint(session['Clear_form']['money_all'])
        ]
    Clear_cont = data_creation(session['Clear_form']['control_time_all'], session['Clear_form']['control_money_all'], batch)
    Handv = [
        strtoint(session['Handv_form']['time_pc']),
        strtoint(session['Handv_form']['time_all']),
        strtoint(session['Handv_form']['money_pc']),
        strtoint(session['Handv_form']['money_all'])
        ]
    Handv_cont = data_creation(session['Handv_form']['control_time_all'], session['Handv_form']['control_money_all'], batch)
    Sep = [
        strtoint(session['Sep_form']['time_pc']),
        strtoint(session['Sep_form']['time_all']),
        strtoint(session['Sep_form']['money_pc']),
        strtoint(session['Sep_form']['money_all'])
        ]
    Xray = [
        strtoint(session['Xray_form']['time_pc']),
        strtoint(session['Xray_form']['time_all']),
        strtoint(session['Xray_form']['money_pc']),
        strtoint(session['Xray_form']['money_all'])
        ]
    
    if "time_pc_ICT" in session['Add_form']:
        if (session["Add_form"]["time_pc_ICT"] != "-") and (session["Add_form"]["time_pc_ICT"] != "0 с"):
            ICT = [
                strtoint(session['Add_form']["time_pc_ICT"]),
                strtoint(session['Add_form']["time_all_ICT"]),
                strtoint(session['Add_form']["money_pc_ICT"]),
                strtoint(session['Add_form']["money_all_ICT"]),
            ]
            Add = [
                strtoint(session['Add_form']['time_pc']) - ICT[0],
                strtoint(session['Add_form']['time_all']) - ICT[1],
                strtoint(session['Add_form']['money_pc']) - ICT[2],
                strtoint(session['Add_form']['money_all']) - ICT[3]
            ]
        else:
            ICT = [
                "-",
                "-",
                "-",
                "-"
            ]
            Add = [
                strtoint(session['Add_form']['time_pc']),
                strtoint(session['Add_form']['time_all']),
                strtoint(session['Add_form']['money_pc']),
                strtoint(session['Add_form']['money_all'])
            ]
    else:
        ICT = [
            "-",
            "-",
            "-",
            "-"
        ]
        Add = [
            strtoint(session['Add_form']['time_pc']),
            strtoint(session['Add_form']['time_all']),
            strtoint(session['Add_form']['money_pc']),
            strtoint(session['Add_form']['money_all'])
        ]
    
    if "Comp_form" in session:
        Contr_out = [
            strtoint(session['Comp_form']['time_pc3']),
            strtoint(session['Comp_form']['time_all3']),
            strtoint(session['Comp_form']['money_pc3']),
            strtoint(session['Comp_form']['money_all3'])
        ]
        End = [
            strtoint(session['Comp_form']['time_pc4']),
            strtoint(session['Comp_form']['time_all4']),
            strtoint(session['Comp_form']['money_pc4']),
            strtoint(session['Comp_form']['money_all4'])
        ]
        Contr_in = [
            strtoint(session['Comp_form']['time_pc2']),
            strtoint(session['Comp_form']['time_all2']),
            strtoint(session['Comp_form']['money_pc2']),
            strtoint(session['Comp_form']['money_all2'])
        ]
        Start = [
            strtoint(session['Comp_form']['time_pc1']),
            strtoint(session['Comp_form']['time_all1']),
            strtoint(session['Comp_form']['money_pc1']),
            strtoint(session['Comp_form']['money_all1'])
        ]
    else:
        Contr_out =[
            "-",
            "-",
            "-",
            "-"
        ]
        End =[
            "-",
            "-",
            "-",
            "-"
        ]
        Contr_in =[
            "-",
            "-",
            "-",
            "-"
        ]
        Start =[
            "-",
            "-",
            "-",
            "-"
        ]
    if "Pack_form" in session:
        if session['Pack_form']['money_pc'] == "-":
            Pack =[
            "-",
            "-",
            "-",
            "-"
        ]
        else:
            Pack = [
                0,
                0,
                strtoint(session['Pack_form']['money_pc']),
                strtoint(session['Pack_form']['money_all'])
            ]
    else:
        Pack =[
            "-",
            "-",
            "-",
            "-"
        ]
    data = [ SMD_re_t, SMD_t, SMD_re_b, SMD_b, SMD_rep, SMD_cont,
            THT_pri_re, THT_pri_p, THT_pri, THT_sec_re, THT_sec_p, THT_sec, THT_rep, THT_cont, 
            Wave_p, Wave, Wave_rep, Wave_cont, 
            HRL_re, HRL, HRL_rep, HRL_cont, 
            Hand, Hand_cont, 
            Test, Clear, Clear_cont, Handv, 
            Handv_cont, Sep, Xray, Add, ICT, Pack, Contr_in, Contr_out, Start, End]
 #           , """Comp""" 
    headers = ["Время на 1 ПУ, с", "Время на партию, ч", "Стоимость 1 ПУ, руб", "Стоимость на партию, руб"]
    #Статьи расходов
    row_headers = [
        "Поверхностный монтаж SMT Pri, переналадка",
        "Автоматический поверхностный монтаж SMT Pri", 
        "Поверхностный монтаж SMT Sec, переналадка",
        "Автоматический поверхностный монтаж SMT Sec", 
        "Ремонт на поверхностном монтаже",
        "Контроль на поверхностном монтаже",

        "Селективная пайка THT Pri, переналадка",
        "Селективная пайка THT Pri, набивка",
        "Селективная пайка THT Pri", 
        "Селективная пайка THT Sec, переналадка",
        "Селективная пайка THT Sec, набивка",
        "Селективная пайка THT Sec", 
        "Ремонт на cелективной пайке THT",
        "Контроль на cелективной пайке THT",

        "Волновая пайка, набивка",
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
        "Доп. работы",
        "ICT",
        "Упаковка", 
        "Входной контроль",
        "Выходной контроль",
        "Приемка",
        "Отгрузка"]
    #Создание DataFrame со значениями выше
    df = pd.DataFrame(data, columns=headers, index=row_headers)
    pc = int(session["second_form"]["pc"])
    df_tech_map = tech_map(df, session, pc)
    df = df.drop(df[(df == "-").all(axis=1)].index)
    sum_time_pc, sum_money_pc, sum_time_all, sum_money_all, sum_time_mz, sum_money_mz = 0, 0, 0, 0, 0, 0
    df["Время на мз, с"] = ""
    df["Стоимость мз, руб"] = ""
    for i in range(df.shape[0]):
        sum_time_pc_temp = int(float(str(df.iloc[i, 0]).split(" ")[0]))
        sum_time_all_temp = int(float(str(df.iloc[i, 1]).split(" ")[0]))
        sum_money_pc_temp = int(float(str(df.iloc[i, 2]).split(" ")[0]))
        sum_money_all_temp = int(float(str(df.iloc[i, 3]).split(" ")[0]))
        df.iloc[i,4] = sum_time_pc_temp * pc
        df.iloc[i,5] = sum_money_pc_temp * pc
        if df.iloc[i]._name:
            sum_time_pc += sum_time_pc_temp
            sum_time_all += sum_time_all_temp
            sum_money_pc += sum_money_pc_temp
            sum_money_all += sum_money_all_temp
            sum_time_mz += df.iloc[i,4]
            sum_money_mz += df.iloc[i,5]
    total = [sum_time_pc, sum_time_all, sum_money_pc, sum_money_all, sum_time_mz, sum_money_mz]
    df.loc["Cебестоимость"] = total #Строка итого
    #Создание таблицы с подоготовкой производства
    prep_sum = 0
    prep_sum_mz = 0
    prep_sum_pc = int(prep_sum / batch)
    Traf = 0
    if 'prepare' in session['second_form']:
        headers2 = ["Наименование","Стоимость, руб"]
        data2 = prepare(session)
        Traf = int(str(data2[0][1]).split(" ")[0])
        for data_in_data2 in data2:
            prep_sum += int(str(data_in_data2[1]).split(" ")[0])
        data2.append(["Итого", prep_sum])
        prep_sum_pc = int(prep_sum / batch)
        prep_sum_mz = prep_sum_pc * pc  
    VAT = int(session["Info_form"]["VAT"]) / 100.0 + 1
    Income = int(session["Info_form"]["Info_proc"]) / 100.0 + 1
    sum = [sum_time_pc, sum_time_all, sum_money_pc, sum_money_all, sum_time_mz, sum_money_mz]
    sum[2] = int(sum[2] * Income)
    sum[3] = int(sum[3] * Income)
    sum[5] = int(sum[5] * Income)
    df.loc["Стоимость с прибылью, без НДС и подготовки"] = [sum[0], sum[1], sum[2], sum[3], sum[4], sum[5]]
    sum[2] = int(sum[2] + prep_sum_pc)
    sum[3] = int(sum[3] + prep_sum)
    sum[5] = int(sum[5] + prep_sum_mz)
    df.loc["Стоимость с прибылью и подготовкой, без НДС"] = [sum[0], sum[1], sum[2], sum[3], sum[4], sum[5]]
    sum[2] = int(sum[2] * VAT)
    sum[3] = int(sum[3] * VAT)
    sum[5] = int(sum[5] * VAT)
    df.loc["Итоговая стоимость"] = [sum[0], sum[1], sum[2], sum[3], sum[4], sum[5]]
    cost_c, cost_e, cost_p = 0, 0, 0
    if "cost_c" in session["second_form"]:
        if session["second_form"]["cost_c"] != "":
            cost_c = int(session["second_form"]["cost_c"])
        if session["second_form"]["cost_e"] != "":
            cost_e = int(session["second_form"]["cost_e"])
        if session["second_form"]["cost_p"] != "":
            cost_p = int(session["second_form"]["cost_p"])
    prep = prep_sum - Traf
    if prep < 0:
        prep = 0
    data3 = [
        ["Трафареты", Traf],
        ["Подготовка производства", prep],
        ["Печатные платы", cost_p],
        ["Компоненты", cost_c],
        ["Оснастки", cost_e],
        ["Итого", cost_p + cost_c + cost_e + prep + Traf]
    ]
    headers3 = ["Наименование", "Стоимость, руб"]
    df3 = pd.DataFrame(data3, columns=headers3)

    columns = ["Время на 1 ПУ, с", "Время на мз, с", "Время на партию, ч", "Стоимость 1 ПУ, руб", "Стоимость мз, руб", "Стоимость на партию, руб"]
    df = df[columns]

    if 'prepare' in session['second_form']:
        df2 = pd.DataFrame(data2, columns=headers2)
        return [df, df2, df3, df_tech_map]
    
    return [df, 1, df3, df_tech_map]

def prepare(session):
    df = pd.read_csv('data/Traf.csv')
    df2 = pd.read_csv('data/tarifs.csv')
    if "Trafs_costs_select" in session["second_form"] and "Traf" in session["second_form"]: #Выбор стоимости трафарет основываясь на том, что было выбрано на странице second
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
    traf = traf
    doc = df2["Стоимость, руб/ч"][23]
    if "tables" in session:
        ebom = df2["Стоимость, руб/ч"][24] * session["tables"][4]
    else:
        ebom = "0 руб"
    return [["Трафареты", traf], ["Проверка документации", doc], ["Создание EBOM", ebom]]


"""Функция для создания значений в массиве при известном одном значении"""   
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
            math.ceil(int(str(time_all).split(" ")[0]) / batch * 3600),
            strtoint(time_all),
            math.ceil(int(str(money_all).split(" ")[0]) / batch),
            strtoint(money_all)
        ]
    return list1

def tech_map(df_calc, session, pc):
    if session['second_form']['prod'] == "1":
        df_wc = pd.read_csv('data/WC_1.csv', encoding='windows-1251', index_col=0)
    else:
        if session['Comp_form']['Comp_type'] == "2": 
            df_wc = pd.read_csv('data/WC_MB.csv', encoding='windows-1251', index_col=0)
        else:
            df_wc = pd.read_csv('data/WC.csv', encoding='windows-1251', index_col=0)
    df_wc.loc['Автоматический поверхностный монтаж SMT Pri', 'Время наладки'] = df_calc.loc["Поверхностный монтаж SMT Pri, переналадка", "Время на партию, ч"]
    df_wc.loc['Автоматический поверхностный монтаж SMT Pri', 'Машинное время (время работы)'] = df_calc.loc["Автоматический поверхностный монтаж SMT Pri", "Время на 1 ПУ, с"]
    df_wc.loc['Автоматический поверхностный монтаж SMT Pri', 'Базовое количество'] = pc

    df_wc.loc['Автоматический поверхностный монтаж SMT Sec', 'Время наладки'] = df_calc.loc["Поверхностный монтаж SMT Sec, переналадка", "Время на партию, ч"]
    df_wc.loc['Автоматический поверхностный монтаж SMT Sec', 'Машинное время (время работы)'] = df_calc.loc["Автоматический поверхностный монтаж SMT Sec", "Время на 1 ПУ, с"]
    df_wc.loc['Автоматический поверхностный монтаж SMT Sec', 'Базовое количество'] = pc

    df_wc.loc['Ремонт после SMT', 'Машинное время (время работы)'] = df_calc.loc["Ремонт на поверхностном монтаже", "Время на 1 ПУ, с"]
    df_wc.loc['Ремонт после SMT', 'Базовое количество'] = pc    
    
    df_wc.loc['Контроль после SMT', 'Машинное время (время работы)'] = df_calc.loc["Контроль на поверхностном монтаже", "Время на 1 ПУ, с"]
    df_wc.loc['Контроль после SMT', 'Базовое количество'] = pc    
    
    
    df_wc.loc['Рентген-контроль', 'Машинное время (время работы)'] = df_calc.loc["Рентгенконтроль", "Время на 1 ПУ, с"]
    df_wc.loc['Контроль после SMT', 'Базовое количество'] = pc    
    
    df_wc.loc['Селективная пайка THT Pri', 'Время наладки'] = df_calc.loc["Селективная пайка THT Pri, переналадка", "Время на партию, ч"]
    df_wc.loc['Селективная пайка THT Pri', 'Машинное время (время работы)'] = df_calc.loc["Селективная пайка THT Pri", "Время на 1 ПУ, с"]
    df_wc.loc['Селективная пайка THT Pri', 'Базовое количество'] = pc    
    
    
    df_wc.loc['Селективная пайка THT Sec', 'Время наладки'] = df_calc.loc["Селективная пайка THT Sec, переналадка", "Время на партию, ч"]
    df_wc.loc['Селективная пайка THT Sec', 'Машинное время (время работы)'] = df_calc.loc["Селективная пайка THT Sec", "Время на 1 ПУ, с"]
    df_wc.loc['Селективная пайка THT Sec', 'Базовое количество'] = pc    
    
    
    df_wc.loc['Ремонт после THT', 'Машинное время (время работы)'] = df_calc.loc["Ремонт на cелективной пайке THT", "Время на 1 ПУ, с"]
    df_wc.loc['Ремонт после THT', 'Базовое количество'] = pc    
    
    df_wc.loc['Контроль после THT', 'Машинное время (время работы)'] = df_calc.loc["Контроль на cелективной пайке THT", "Время на 1 ПУ, с"]
    df_wc.loc['Контроль после THT', 'Базовое количество'] = pc

    df_wc.loc['Набивка компонентов Pri', 'Машинное время (время работы)'] = df_calc.loc["Селективная пайка THT Pri, набивка", "Время на 1 ПУ, с"]
    df_wc.loc['Набивка компонентов Pri', 'Базовое количество'] = pc

    df_wc.loc['Набивка компонентов Sec', 'Машинное время (время работы)'] = df_calc.loc["Селективная пайка THT Sec, набивка", "Время на 1 ПУ, с"]
    df_wc.loc['Набивка компонентов Sec', 'Базовое количество'] = pc


    df_wc.loc['Набивка компонентов волна', 'Машинное время (время работы)'] = df_calc.loc["Волновая пайка, набивка", "Время на 1 ПУ, с"]
    df_wc.loc['Набивка компонентов волна', 'Базовое количество'] = pc    
    
    df_wc.loc['Волновая пайка', 'Машинное время (время работы)'] = df_calc.loc["Волновая пайка", "Время на 1 ПУ, с"]
    df_wc.loc['Волновая пайка', 'Базовое количество'] = pc    
    
    df_wc.loc['Ремонт на волновой пайке', 'Машинное время (время работы)'] = df_calc.loc["Ремонт на волновой пайке", "Время на 1 ПУ, с"]
    df_wc.loc['Ремонт на волновой пайке', 'Базовое количество'] = pc    
    
    df_wc.loc['Контроль на волновой пайке', 'Машинное время (время работы)'] = df_calc.loc["Контроль на волновой пайке", "Время на 1 ПУ, с"]
    df_wc.loc['Контроль на волновой пайке', 'Базовое количество'] = pc    

    
    df_wc.loc['Селективная влагозащита HRL', 'Машинное время (время работы)'] = df_calc.loc["Селективная лакировка HRL", "Время на 1 ПУ, с"]
    df_wc.loc['Селективная влагозащита HRL', 'Базовое количество'] = pc

    df_wc.loc['Рентген-контроль', 'Машинное время (время работы)'] = df_calc.loc["Рентгенконтроль", "Время на 1 ПУ, с"]
    df_wc.loc['Рентген-контроль', 'Базовое количество'] = pc    

    
    df_wc.loc['Разделение', 'Машинное время (время работы)'] = df_calc.loc["Разделение", "Время на 1 ПУ, с"]
    df_wc.loc['Разделение', 'Базовое количество'] = pc

    df_wc.loc['Ручная пайка', 'Машинное время (время работы)'] = df_calc.loc["Ручной монтаж", "Время на 1 ПУ, с"]
    df_wc.loc['Отмывка', 'Машинное время (время работы)'] = df_calc.loc["Отмывка", "Время на 1 ПУ, с"]
    df_wc.loc['ICT', 'Машинное время (время работы)'] = df_calc.loc["ICT", "Время на 1 ПУ, с"]
    # df_wc.loc['Доп операции', 'Машинное время (время работы)'] = df_calc.loc["Доп. работы", "Время на 1 ПУ, с"]
    df_wc.loc['Тестирование', 'Машинное время (время работы)'] = df_calc.loc["Тестирование", "Время на 1 ПУ, с"]
    df_wc.loc['Влагозащита', 'Машинное время (время работы)'] = df_calc.loc["Ручная лакировка", "Время на 1 ПУ, с"]

    df_wc.loc['Выходной контроль', 'Машинное время (время работы)'] = df_calc.loc["Выходной контроль", "Время на 1 ПУ, с"]
    df_wc.loc['Отгрузка', 'Машинное время (время работы)'] = df_calc.loc["Отгрузка", "Время на 1 ПУ, с"]
    df_wc.index.name = 'Текст операции'
    df_wc[['Время наладки', 'Машинное время (время работы)']] = df_wc[['Время наладки', 'Машинное время (время работы)']].fillna(0)
    df_wc = df_wc.fillna("")
    df_wc = df_wc[df_wc['Машинное время (время работы)'] != "-"]
    df_wc = df_wc.reset_index()   # Сбрасываем индекс
    df_wc['Номер операции'] = (df_wc.index + 1) * 10  # Создаем новый столбец с номерами операций

    # Проверяем наличие столбца 'Текст операции'
    if 'Текст операции' in df_wc.columns:
        # Переставляем столбцы так, чтобы 'Номер операции' был первым, а 'Текст операции' последним
        df_wc = df_wc[['Номер операции'] + [col for col in df_wc.columns if col not in ['Номер операции', 'Текст операции']] + ['Текст операции']]
    else:
        print("Столбец 'Текст операции' отсутствует в DataFrame.")
        # Здесь можно добавить логику обработки, если столбец отсутствует
    df_wc = df_wc.set_index(df_wc.columns[0])



    
    
    return df_wc