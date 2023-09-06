import pandas as pd
""" 
Функция для того, чтобы понять сколько компонентов ставится на какую сторону. на Входе - тблица с 4мя столбцами. 2 Первые 2 столбца - PAP, вторые - BOM
Сначала разбиваем исходную таблицу на 2: PAP и BOM, затем в PAP разбивается по сторона установки на TOP и BOT и ищется соответсвие в ВОМ. Если соответствие находится, то прописывается наименование.
Позже по количеству наименований считается количество уникальных компонентов, устанавливаемых на разные стороны
"""
def tables(file):
    df = pd.read_csv(file, encoding='utf-8', sep=',')
    PAP = df.iloc[:, :2] #Выделяем таблицу PAP
    BOM = df.iloc[:, 2:] #Выделяем таблицу BOM
    Bot = PAP[PAP["Layer"] == 'Bot']["Designator"] #Из таблицы PAP выделяем те компоненты, которые ставятся на сторону Bot
    Bot = pd.DataFrame(Bot)
    Top = PAP[PAP["Layer"] == 'Top']["Designator"] #Из таблицы PAP выделяем те компоненты, которые ставятся на сторону Top
    Top = pd.DataFrame(Top)
    top_lines = 0
    bot_lines = 0
    BOM.dropna(axis='index', how='all', inplace=True) #Выкидываем пустые строки. Т.к. ВОМ всегда не больше РАР, а для удобства обработки мы закидываем всё одной таблицей
    unics = BOM.shape[0] #Подсчёт количества строк в ВОМ
    for index, row in Bot.iterrows(): #Проходимся по по всем ссылочным указателям в Bot, чтобы проверить есть они в BOM или нет. Часто бывает, что PAP больше, чем BOM и там будут незаполненные строки
        value = str(row['Designator'])
        for index2, row2, in BOM.iterrows():
            value2 = str(row2['Designators (BOM)']).replace(" ","").split(",") #Разделяем строку со ссылочными указателями в ВОМ по запятым, так же убираем пробелы и запятые 
            if value in value2:
                Bot.at[index, 'Name'] = row2["Name"]
                bot_lines += 1 #Счётчик количества устанавливаемых компонентов
    for index, row in Top.iterrows():
        value = str(row['Designator'])
        for index2, row2, in BOM.iterrows():
            value2 = str(row2['Designators (BOM)']).replace(" ","").split(",")
            if value in value2:
                Top.at[index, 'Name'] = row2["Name"]
                top_lines += 1
    if top_lines != 0:
        top_lines_unic = Top["Name"].nunique() #Количество уникальных компонентов на стороне TOP
    else:
        top_lines_unic = 0
    if bot_lines != 0:
        bot_lines_unic = Bot["Name"].nunique()
    else:
        bot_lines_unic = 0
    lines = [top_lines, #Количество компонентов на стороне Top 
             top_lines_unic, #Количество уникальных компонентов на стороне Top
             bot_lines, #Количество компонентов на стороне Bot
             bot_lines_unic, #Количество уникальных компонентов на стороне Воt
             unics] #Количество компонентов в ВОМ
    return lines

"""Функция для сохранения изменений в таблице коэффициентов, которые были внесены в веб версии"""
def update_table(name, form, df):
    for key in form.keys():
        if key.startswith('row'):  # если используется имя вида 'row%d'
            row = int(key[3:])  # извлекаем номер строки из имени
            df["Значение"][row] = form[key]  # обновляем значение ячейки
    name = "data/"+name+".csv"        
    df.to_csv(name, index=False)