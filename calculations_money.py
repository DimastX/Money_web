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

def calculate_component_based_cost(session):
    """
    Рассчитывает стоимость изготовления на основе количества компонентов.
    """
    
    try:
        batch = int(session.get('home_form', {}).get('field3', 0))
    except (ValueError, TypeError):
        batch = 0
        
    if batch == 0:
        return 0, pd.DataFrame()

    # Получение данных из сессии с преобразованием в int и обработкой отсутствующих ключей
    smd_form = session.get('SMD_form', {})
    smd1 = int(smd_form.get('SMD1', 0) or 0)
    smd3 = int(smd_form.get('SMD3', 0) or 0)
    
    comp_form = session.get('Comp_form', {})
    # SMD5 - количество наименований
    smd5 = int(comp_form.get('Comp_num', 0) or 0)

    tht_form = session.get('THT_form', {})
    points = int(tht_form.get('points', 0) or 0) 
    points_2 = int(tht_form.get('points_2', 0) or 0)
    points2 = int(tht_form.get('points2', 0) or 0)
    points2_2 = int(tht_form.get('points2_2', 0) or 0)
    ddr = int(tht_form.get('DDR', 0) or 0)
    ddr_2 = int(tht_form.get('DDR2', 0) or 0)
    pci = int(tht_form.get('PCI', 0) or 0)
    pci_2 = int(tht_form.get('PCI2', 0) or 0)
    
    hand_form = session.get('Hand_form', {})
    hand_num = int(hand_form.get('Hand_num', 0) or 0)

    test_form = session.get('Test_form', {})
    num_0 = int(test_form.get('num_0', 0) or 0)

    comp_type_str = comp_form.get('Comp_type', '0')
    comp_type = int(comp_type_str) if comp_type_str.isdigit() else 0

    # Начало расчёта
    costs = {}

    # 1. Стоимость SMD
    is_server_or_mb = comp_type in [1, 2]
    smd_components = (smd1 + smd3) * batch
    if is_server_or_mb:
        costs['SMD'] = smd_components * 0.3
    else:  # Обычная плата (типы 3, 4 или другие)
        costs['SMD'] = smd_components * 0.3

    # 2. Стоимость переналадки SMD
    costs['SMD переналадка'] = smd5 * 504.0

    # 3. Стоимость THT
    costs['THT (pin)'] = (points + points2) * batch * 12.7
    costs['THT (pin2)'] = (points_2 + points2_2) * batch * 30.0
    costs['THT (DDR)'] = (ddr + ddr_2) * batch * 72.0
    costs['THT (PCI)'] = (pci + pci_2) * batch * 37.0

    # 4. Стоимость ручных операций
    costs['Ручные операции'] = hand_num * batch * 3.5

    # 5. Стоимость прошивки
    costs['Прошивка'] = num_0 * batch * 9.0

    # Тестирование
    # if comp_type == 1:  # Сервер
    #     costs['Тестирование'] = smd_components * 0.18
    # elif comp_type == 2:  # Материнская плата
    #     costs['Тестирование'] = smd_components * 0.11
    # else:  # Обычная плата
    #     costs['Тестирование'] = smd_components * 0.75

    total_cost_before_markup = sum(costs.values())

    # 6. Наценка
    if comp_type == 1:  # Серверная плата
        markup = total_cost_before_markup * 0.48
        total_cost = total_cost_before_markup + markup
        # Дополнительная корректировка: уменьшить на 10% от итогового значения
        total_cost = total_cost / 1.09
    elif comp_type == 2:  # Материнская плата
        markup = total_cost_before_markup * 0.48
        total_cost = total_cost_before_markup + markup
        # Дополнительная корректировка: увеличить на 36% от итогового значения
        total_cost = total_cost / 0.64
    elif comp_type == 3:  # Обычная плата (тип 3)
        markup = total_cost_before_markup * 0.4
        total_cost = total_cost_before_markup + markup
        # Дополнительная корректировка: увеличить на 38% от итогового значения
        total_cost = total_cost / 0.62
    elif comp_type == 4:  # Маленькая плата (тип 4)
        markup = total_cost_before_markup * 0.4
        total_cost = total_cost_before_markup + markup
        # Дополнительная корректировка: увеличить на 22% от итогового значения
        total_cost = total_cost / 0.78
    costs['Итого, с остальными операциями'] = total_cost
    
    # Округление до целых чисел
    for key in costs:
        costs[key] = int(round(costs[key], 0))
    
    # Создание DataFrame для вывода
    df_costs = pd.DataFrame(costs.items(), columns=['Наименование', 'Стоимость, руб'])


    return int(round(total_cost, 0)), df_costs

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
    if session['SMD_form'].get('repair_time_all_t', "-") != '-':
        SMD_rep_t = data_creation(session['SMD_form'].get('repair_time_all_t', "-"), session['SMD_form'].get('repair_money_all_t', "-"), batch)
        SMD_cont_t = data_creation(session['SMD_form'].get('control_time_all_t', "-"), session['SMD_form'].get('control_money_all_t', "-"), batch)
        SMD_rep_b = data_creation(session['SMD_form'].get('repair_time_all_b', "-"), session['SMD_form'].get('repair_money_all_b', "-"), batch)
        SMD_cont_b = data_creation(session['SMD_form'].get('control_time_all_b', "-"), session['SMD_form'].get('control_money_all_b', "-"), batch)
    else:
        SMD_rep_t =["-", "-", "-", "-"]
        SMD_cont_t =["-", "-", "-", "-"]
        SMD_rep_b =["-", "-", "-", "-"]
        SMD_cont_b =["-", "-", "-", "-"]

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
    THT_rep_p = data_creation(session['THT_form'].get('repair_time_all_p', "-"), session['THT_form'].get('repair_money_all_p', "-"), batch)
    THT_cont_p = data_creation(session['THT_form'].get('control_time_all_p', "-"), session['THT_form'].get('control_money_all_p', "-"), batch)
    THT_rep_s = data_creation(session['THT_form'].get('repair_time_all_s', "-"), session['THT_form'].get('repair_money_all_s', "-"), batch)
    THT_cont_s = data_creation(session['THT_form'].get('control_time_all_s', "-"), session['THT_form'].get('control_money_all_s', "-"), batch)
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
    data = [ SMD_re_t, SMD_t, SMD_rep_t, SMD_cont_t, SMD_re_b, SMD_b, SMD_rep_b, SMD_cont_b,
            THT_pri_re, THT_pri_p, THT_pri, THT_rep_p, THT_cont_p, THT_sec_re, THT_sec_p, THT_sec, THT_rep_s, THT_cont_s,
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
        "Ремонт на поверхностном монтаже Pri",
        "Контроль на поверхностном монтаже Pri",
        "Поверхностный монтаж SMT Sec, переналадка",
        "Автоматический поверхностный монтаж SMT Sec", 
        "Ремонт на поверхностном монтаже Sec",
        "Контроль на поверхностном монтаже Sec",

        "Селективная пайка THT Pri, переналадка",
        "Селективная пайка THT Pri, набивка",
        "Селективная пайка THT Pri", 
        "Ремонт на cелективной пайке THT Pri",
        "Контроль на cелективной пайке THT Pri",
        "Селективная пайка THT Sec, переналадка",
        "Селективная пайка THT Sec, набивка",
        "Селективная пайка THT Sec",
        "Ремонт на cелективной пайке THT Sec",
        "Контроль на cелективной пайке THT Sec",

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
    
    component_cost, df_component_cost = calculate_component_based_cost(session)
    
    prime_cost_batch = df.loc["Cебестоимость", "Стоимость на партию, руб"]
    difference = component_cost - prime_cost_batch
    if prime_cost_batch > 0:
        difference_percent = f"{round((difference / prime_cost_batch) * 100, 2)}%"
    else:
        difference_percent = "-"
        
    new_rows = pd.DataFrame([
        {'Наименование': 'Разница', 'Стоимость, руб': difference},
        {'Наименование': 'Разница в %', 'Стоимость, руб': difference_percent}
    ])
    df_component_cost = pd.concat([df_component_cost, new_rows], ignore_index=True)


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
        return [df, df2, df3, df_tech_map, df_component_cost]
    
    return [df, 1, df3, df_tech_map, df_component_cost]

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
    
    # Helper function to safely get and calculate machine time
    def get_calculated_machine_time(source_row_name):
        val = df_calc.loc[source_row_name, "Время на 1 ПУ, с"]
        return (int(val) * pc) if val != "-" else 0

    df_wc.loc['Автоматический поверхностный монтаж SMT Pri', 'Время наладки'] = df_calc.loc["Поверхностный монтаж SMT Pri, переналадка", "Время на партию, ч"]
    df_wc.loc['Автоматический поверхностный монтаж SMT Pri', 'Машинное время (время работы)'] = get_calculated_machine_time("Автоматический поверхностный монтаж SMT Pri")
    df_wc.loc['Автоматический поверхностный монтаж SMT Pri', 'Базовое количество'] = pc

    df_wc.loc['Автоматический поверхностный монтаж SMT Sec', 'Время наладки'] = df_calc.loc["Поверхностный монтаж SMT Sec, переналадка", "Время на партию, ч"]
    df_wc.loc['Автоматический поверхностный монтаж SMT Sec', 'Машинное время (время работы)'] = get_calculated_machine_time("Автоматический поверхностный монтаж SMT Sec")
    df_wc.loc['Автоматический поверхностный монтаж SMT Sec', 'Базовое количество'] = pc

    df_wc.loc['Ремонт после SMT Pri', 'Машинное время (время работы)'] = get_calculated_machine_time("Ремонт на поверхностном монтаже Pri")
    df_wc.loc['Ремонт после SMT Pri', 'Базовое количество'] = pc    
    
    df_wc.loc['Контроль после SMT Pri', 'Машинное время (время работы)'] = get_calculated_machine_time("Контроль на поверхностном монтаже Pri")
    df_wc.loc['Контроль после SMT Pri', 'Базовое количество'] = pc    
    
    df_wc.loc['Ремонт после SMT Sec', 'Машинное время (время работы)'] = get_calculated_machine_time("Ремонт на поверхностном монтаже Sec")
    df_wc.loc['Ремонт после SMT Sec', 'Базовое количество'] = pc    
    
    df_wc.loc['Контроль после SMT Sec', 'Машинное время (время работы)'] = get_calculated_machine_time("Контроль на поверхностном монтаже Sec")
    df_wc.loc['Контроль после SMT Sec', 'Базовое количество'] = pc    
    
    df_wc.loc['Рентген-контроль', 'Машинное время (время работы)'] = get_calculated_machine_time("Рентгенконтроль")
    df_wc.loc['Рентген-контроль', 'Базовое количество'] = pc    
    
    df_wc.loc['Селективная пайка THT Pri', 'Время наладки'] = df_calc.loc["Селективная пайка THT Pri, переналадка", "Время на партию, ч"]
    df_wc.loc['Селективная пайка THT Pri', 'Машинное время (время работы)'] = get_calculated_machine_time("Селективная пайка THT Pri")
    df_wc.loc['Селективная пайка THT Pri', 'Базовое количество'] = pc    
    
    
    df_wc.loc['Селективная пайка THT Sec', 'Время наладки'] = df_calc.loc["Селективная пайка THT Sec, переналадка", "Время на партию, ч"]
    df_wc.loc['Селективная пайка THT Sec', 'Машинное время (время работы)'] = get_calculated_machine_time("Селективная пайка THT Sec")
    df_wc.loc['Селективная пайка THT Sec', 'Базовое количество'] = pc    
    
    
    df_wc.loc['Ремонт после THT Pri', 'Машинное время (время работы)'] = get_calculated_machine_time("Ремонт на cелективной пайке THT Pri")
    df_wc.loc['Ремонт после THT Pri', 'Базовое количество'] = pc    
    
    df_wc.loc['Контроль после THT Pri', 'Машинное время (время работы)'] = get_calculated_machine_time("Контроль на cелективной пайке THT Pri")
    df_wc.loc['Контроль после THT Pri', 'Базовое количество'] = pc

    df_wc.loc['Ремонт после THT Sec', 'Машинное время (время работы)'] = get_calculated_machine_time("Ремонт на cелективной пайке THT Sec")
    df_wc.loc['Ремонт после THT Sec', 'Базовое количество'] = pc    
    
    df_wc.loc['Контроль после THT Sec', 'Машинное время (время работы)'] = get_calculated_machine_time("Контроль на cелективной пайке THT Sec")
    df_wc.loc['Контроль после THT Sec', 'Базовое количество'] = pc

    df_wc.loc['Набивка компонентов Pri', 'Машинное время (время работы)'] = get_calculated_machine_time("Селективная пайка THT Pri, набивка")
    df_wc.loc['Набивка компонентов Pri', 'Базовое количество'] = pc

    df_wc.loc['Набивка компонентов Sec', 'Машинное время (время работы)'] = get_calculated_machine_time("Селективная пайка THT Sec, набивка")
    df_wc.loc['Набивка компонентов Sec', 'Базовое количество'] = pc


    df_wc.loc['Набивка компонентов волна', 'Машинное время (время работы)'] = get_calculated_machine_time("Волновая пайка, набивка")
    df_wc.loc['Набивка компонентов волна', 'Базовое количество'] = pc    
    
    df_wc.loc['Волновая пайка', 'Машинное время (время работы)'] = get_calculated_machine_time("Волновая пайка")
    df_wc.loc['Волновая пайка', 'Базовое количество'] = pc    
    
    df_wc.loc['Ремонт на волновой пайке', 'Машинное время (время работы)'] = get_calculated_machine_time("Ремонт на волновой пайке")
    df_wc.loc['Ремонт на волновой пайке', 'Базовое количество'] = pc    
    
    df_wc.loc['Контроль на волновой пайке', 'Машинное время (время работы)'] = get_calculated_machine_time("Контроль на волновой пайке")
    df_wc.loc['Контроль на волновой пайке', 'Базовое количество'] = pc    

    
    df_wc.loc['Селективная влагозащита HRL', 'Машинное время (время работы)'] = get_calculated_machine_time("Селективная лакировка HRL")
    df_wc.loc['Селективная влагозащита HRL', 'Базовое количество'] = pc

    df_wc.loc['Рентген-контроль', 'Машинное время (время работы)'] = get_calculated_machine_time("Рентгенконтроль")
    df_wc.loc['Рентген-контроль', 'Базовое количество'] = pc    

    
    df_wc.loc['Разделение', 'Машинное время (время работы)'] = get_calculated_machine_time("Разделение")
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
    df_wc = df_wc[df_wc['Машинное время (время работы)'] != 0]
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