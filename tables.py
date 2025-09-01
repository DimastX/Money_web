import pandas as pd
import logging
import time

# === ОБРАБОТКА СПЕЦИФИКАЦИЙ PAP И BOM ===
""" 
Функция для того, чтобы понять сколько компонентов ставится на какую сторону. на Входе - тблица с 4мя столбцами. 2 Первые 2 столбца - PAP, вторые - BOM
Сначала разбиваем исходную таблицу на 2: PAP и BOM, затем в PAP разбивается по сторона установки на TOP и BOT и ищется соответсвие в ВОМ. Если соответствие находится, то прописывается наименование.
Позже по количеству наименований считается количество уникальных компонентов, устанавливаемых на разные стороны
"""
def tables(file):
    start_time = time.time()
    logging.info("Начало обработки таблицы")
    
    try:
        # Чтение данных из Excel файла
        df = pd.read_excel(file)
        logging.info(f"Файл прочитан, размер: {df.shape}")
        
        # Разделение исходного DataFrame на PAP (первые 2 столбца) и BOM (следующие столбцы)
        PAP = df.iloc[:, :2] 
        BOM = df.iloc[:, 2:] 
        
        # Обработка таблицы PAP
        PAP['Layer'] = PAP['Layer'].fillna("") # Заполнение пустых значений в столбце 'Layer' пустой строкой
        PAP = PAP.drop_duplicates() # Удаление дубликатов в PAP
        
        # Приведение названий слоев к нижнему регистру для унификации
        PAP['Layer_lower'] = PAP['Layer'].str.lower()

        # Проверка на наличие некорректных слоев
        all_layers = PAP['Layer_lower'].unique()
        # Удаляем пустые строки и валидные слои, чтобы найти некорректные
        invalid_layers = [layer for layer in all_layers if layer and layer not in ['top', 'bot']]
        
        if invalid_layers:
            logging.error(f"Найдены некорректные слои: {', '.join(invalid_layers)}. Допускаются только 'Top' и 'Bot'.")
            return 0

        # Отбор только строк, где слой 'top' или 'bot'
        valid_layers_df = PAP[PAP['Layer_lower'].isin(['top', 'bot'])]
        
        if valid_layers_df.empty:
            logging.error("Не найдены слои 'Top' или 'Bot' в файле.")
            return 0
        
        found_layers = valid_layers_df['Layer_lower'].unique()
        logging.info(f"Найдены слои: {found_layers}")

        # Выделение компонентов для стороны BOT
        Bot_df = pd.DataFrame()
        if 'bot' in found_layers:
            Bot_components_pap = valid_layers_df[valid_layers_df["Layer_lower"] == 'bot']["Designator"]
            Bot_df = pd.DataFrame(Bot_components_pap)
            Bot_df.rename(columns={'Designator': 'Designator'}, inplace=True)

        # Выделение компонентов для стороны TOP
        Top_df = pd.DataFrame()
        if 'top' in found_layers:
            Top_components_pap = valid_layers_df[valid_layers_df["Layer_lower"] == 'top']["Designator"]
            Top_df = pd.DataFrame(Top_components_pap)
            Top_df.rename(columns={'Designator': 'Designator'}, inplace=True)

        # Обработка таблицы BOM
        BOM = BOM.dropna(axis='index', how='all') # Удаление полностью пустых строк из BOM
        unique_names_bom = BOM["Name"].nunique() # Подсчет количества уникальных наименований в BOM
        
        logging.info(f"BOT компонентов: {len(Bot_df)}, TOP компонентов: {len(Top_df)}, BOM строк: {len(BOM)}")
        
        # === ОПТИМИЗИРОВАННОЕ СОПОСТАВЛЕНИЕ ===
        # Вместо вложенных циклов используем операции pandas
        
        # Создаем словарь для быстрого поиска имен по designator
        designator_to_name = {}
        
        for index_bom, row_bom in BOM.iterrows():
            designators_bom_str = str(row_bom['Designators (BOM)']).replace(" ", "")
            if designators_bom_str != 'nan' and designators_bom_str:
                designators_list = designators_bom_str.split(",")
                for designator in designators_list:
                    if designator.strip():
                        designator_to_name[designator.strip()] = row_bom["Name"]
        
        logging.info(f"Создан словарь с {len(designator_to_name)} соответствиями")
        
        # Быстрое сопоставление для BOT компонентов
        bot_lines_count = 0
        if not Bot_df.empty:
            Bot_df['Name'] = Bot_df['Designator'].astype(str).map(designator_to_name)
            bot_lines_count = int(Bot_df['Name'].notna().sum())
        
        # Быстрое сопоставление для TOP компонентов  
        top_lines_count = 0
        if not Top_df.empty:
            Top_df['Name'] = Top_df['Designator'].astype(str).map(designator_to_name)
            top_lines_count = int(Top_df['Name'].notna().sum())
                    
        # Подсчет уникальных наименований для каждой стороны
        top_lines_unique_count = 0
        if not Top_df.empty and 'Name' in Top_df.columns: # Проверка на существование столбца Name
            top_lines_unique_count = int(Top_df["Name"].nunique())
            
        bot_lines_unique_count = 0
        if not Bot_df.empty and 'Name' in Bot_df.columns: # Проверка на существование столбца Name
            bot_lines_unique_count = int(Bot_df["Name"].nunique())

        # Формирование списка с результатами подсчета
        # Важно: конвертируем все в обычные Python int для JSON сериализации
        result_counts = [
            int(bot_lines_count),      # Общее количество компонентов на стороне Bot
            int(bot_lines_unique_count), # Количество уникальных наименований на стороне Bot
            int(top_lines_count),      # Общее количество компонентов на стороне Top 
            int(top_lines_unique_count), # Количество уникальных наименований на стороне Top
            int(unique_names_bom)      # Общее количество уникальных наименований в BOM
        ]
        
        end_time = time.time()
        processing_time = end_time - start_time
        logging.info(f"Обработка завершена за {processing_time:.2f} секунд. Результат: {result_counts}")
        
        return result_counts
        
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        logging.error(f"Ошибка при обработке таблицы за {processing_time:.2f} секунд: {e}")
        return 0

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