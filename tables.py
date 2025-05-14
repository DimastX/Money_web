import pandas as pd

# === ОБРАБОТКА СПЕЦИФИКАЦИЙ PAP И BOM ===
""" 
Функция для того, чтобы понять сколько компонентов ставится на какую сторону. на Входе - тблица с 4мя столбцами. 2 Первые 2 столбца - PAP, вторые - BOM
Сначала разбиваем исходную таблицу на 2: PAP и BOM, затем в PAP разбивается по сторона установки на TOP и BOT и ищется соответсвие в ВОМ. Если соответствие находится, то прописывается наименование.
Позже по количеству наименований считается количество уникальных компонентов, устанавливаемых на разные стороны
"""
def tables(file):
    # Чтение данных из Excel файла
    # df = pd.read_csv(file, encoding='utf-8', sep=',') # Старый вариант с CSV
    df = pd.read_excel(file)
    
    # Разделение исходного DataFrame на PAP (первые 2 столбца) и BOM (следующие столбцы)
    PAP = df.iloc[:, :2] 
    BOM = df.iloc[:, 2:] 
    
    # Обработка таблицы PAP
    PAP['Layer'] = PAP['Layer'].fillna("") # Заполнение пустых значений в столбце 'Layer' пустой строкой
    PAP.drop_duplicates() # Удаление дубликатов в PAP
    
    # Определение уникальных слоев (сторон установки) из PAP
    Layer = PAP["Layer"].unique()
    Layer = list(filter(None, Layer)) # Удаление пустых значений из списка слоев
    
    # Проверка: если слоев больше двух, формат некорректен
    if len(Layer) > 2:
        return  0 # Возвращаем 0 как признак ошибки
    
    # Выделение компонентов для стороны BOT (первый слой в списке Layer)
    Bot_components_pap = PAP[PAP["Layer"] == Layer[0]]["Designator"]
    Bot_df = pd.DataFrame(Bot_components_pap) # Создание DataFrame для компонентов BOT
    Bot_df.rename(columns={'Designator': 'Designator'}, inplace=True) # Явное именование столбца

    Top_df = pd.DataFrame() # Инициализация DataFrame для TOP компонентов
    if len(Layer) == 2:
        # Выделение компонентов для стороны TOP (второй слой в списке Layer), если он есть
        Top_components_pap = PAP[PAP["Layer"] == Layer[1]]["Designator"]
        Top_df = pd.DataFrame(Top_components_pap)
        Top_df.rename(columns={'Designator': 'Designator'}, inplace=True) # Явное именование столбца

    top_lines_count = 0 # Счетчик компонентов на стороне TOP
    bot_lines_count = 0 # Счетчик компонентов на стороне BOT
    
    # Обработка таблицы BOM
    BOM.dropna(axis='index', how='all', inplace=True) # Удаление полностью пустых строк из BOM
    # bom_table(BOM) # Вызов функции для замены диапазонов (например, C1-C5) на отдельные позиционные обозначения - сейчас закомментировано. 
    # ПОЧЕМУ?????
    unique_names_bom = BOM["Name"].nunique() # Подсчет количества уникальных наименований в BOM
    
    # Сопоставление компонентов BOT из PAP с BOM
    for index_bot, row_bot in Bot_df.iterrows():
        designator_bot = str(row_bot['Designator'])
        for index_bom, row_bom in BOM.iterrows():
            # Преобразование строки с позиционными обозначениями из BOM в список
            designators_bom_list = str(row_bom['Designators (BOM)']).replace(" ","").split(",")
            if designator_bot in designators_bom_list:
                Bot_df.at[index_bot, 'Name'] = row_bom["Name"] # Добавление наименования компонента из BOM
                bot_lines_count += 1
                break # Переход к следующему компоненту BOT после нахождения соответствия
    
    # Сопоставление компонентов TOP из PAP с BOM (если сторона TOP существует)
    if not Top_df.empty:        
        for index_top, row_top in Top_df.iterrows():
            designator_top = str(row_top['Designator'])
            for index_bom, row_bom in BOM.iterrows():
                designators_bom_list = str(row_bom['Designators (BOM)']).replace(" ","").split(",")
                if designator_top in designators_bom_list:
                    Top_df.at[index_top, 'Name'] = row_bom["Name"]
                    top_lines_count += 1
                    break
                    
    # Подсчет уникальных наименований для каждой стороны
    top_lines_unique_count = 0
    if not Top_df.empty and 'Name' in Top_df.columns: # Проверка на существование столбца Name
        top_lines_unique_count = Top_df["Name"].nunique()
        
    bot_lines_unique_count = 0
    if not Bot_df.empty and 'Name' in Bot_df.columns: # Проверка на существование столбца Name
        bot_lines_unique_count = Bot_df["Name"].nunique()

    # Формирование списка с результатами подсчета
    result_counts = [
        top_lines_count,      # Общее количество компонентов на стороне Top 
        top_lines_unique_count, # Количество уникальных наименований на стороне Top
        bot_lines_count,      # Общее количество компонентов на стороне Bot
        bot_lines_unique_count, # Количество уникальных наименований на стороне Bot
        unique_names_bom      # Общее количество уникальных наименований в BOM
    ]
    return result_counts

# === ОБНОВЛЕНИЕ ТАБЛИЦ КОЭФФИЦИЕНТОВ ===

# --- Обновление CSV файла с коэффициентами (таблица с одним столбцом "Значение") Чем отличается от 2ой функции?---
def update_table(csv_name, form_data, df_to_update):
    # Перебор ключей из данных формы
    for key in form_data.keys():
        if key.startswith('row'):  # Ожидается, что ключи для строк начинаются с 'row' (например, 'row0', 'row1')
            row_index = int(key[3:])  # Извлечение номера строки из ключа
            df_to_update.loc[row_index, "Значение"] = form_data[key]  # Обновление значения в DataFrame
    # Формирование полного пути к файлу и сохранение DataFrame в CSV
    file_path = "data/" + csv_name + ".csv"        
    df_to_update.to_csv(file_path, index=False)

# --- Обновление CSV файла с коэффициентами (таблица с несколькими столбцами) ---
def update_table2(csv_name, form_data, df_to_update):
    # Перебор ключей из данных формы
    for key in form_data.keys():
        if key.startswith('row_'):  # Ожидается, что ключи для ячеек имеют формат 'row_ROWINDEX_COLINDEX'
            indices_str = key[4:]  # Извлечение части строки с индексами
            row_idx_str, col_idx_str = indices_str.split("_") # Разделение на индекс строки и столбца
            # Обновление значения в DataFrame по индексам строки и столбца (индекс столбца уменьшается на 1)
            df_to_update.iloc[int(row_idx_str), int(col_idx_str) - 1] = form_data[key]  
    # Формирование полного пути к файлу и сохранение DataFrame в CSV
    file_path = "data/" + csv_name + ".csv"      
    df_to_update.to_csv(file_path, index=False)


# === ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ОБРАБОТКИ BOM ===

# --- Замена диапазонов позиционных обозначений на отдельные значения (например, "C1-C3" -> "C1,C2,C3") ---
# Примечание: Эта функция в текущей версии файла tables.py закомментирована в функции tables()
# def bom_table(BOM_df):
#     for index, row in BOM_df.iterrows():
#         if pd.notna(row['Designators (BOM)']) and '-' in str(row['Designators (BOM)']):
#             designators_str = str(row['Designators (BOM)'])
#             parts = designators_str.split('-')
#             if len(parts) == 2: # Простой диапазон типа R1-R5
#                 prefix_start = ''.join(c for c in parts[0] if c.isalpha() or c == '_') # Префикс типа R, C, DA
#                 num_start_str = ''.join(c for c in parts[0] if c.isdigit())
#                 num_end_str = ''.join(c for c in parts[1] if c.isdigit())
#                 
#                 # Проверка, что префикс одинаковый (на случай C1-R5 - некорректно)
#                 prefix_end = ''.join(c for c in parts[1] if c.isalpha() or c == '_')
#                 if (prefix_end != "" and prefix_start != prefix_end) or not num_start_str or not num_end_str:
#                     # Некорректный диапазон или разные префиксы, оставляем как есть или логируем ошибку
#                     continue 

#                 try:
#                     start_num = int(num_start_str)
#                     end_num = int(num_end_str)
#                     if start_num > end_num:
#                         continue # Некорректный диапазон (начало больше конца)

#                     expanded_designators = [f"{prefix_start}{i}" for i in range(start_num, end_num + 1)]
#                     BOM_df.at[index, 'Designators (BOM)'] = ",".join(expanded_designators)
#                 except ValueError:
#                     # Ошибка преобразования в число, оставляем как есть
#                     continue
#             # Более сложные случаи с несколькими диапазонами или смешанным форматом не обрабатываются здесь
#             # и предполагается, что они уже разделены запятыми или будут обработаны вручную.