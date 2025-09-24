import pickle
from datetime import datetime
import os
import sqlite3
import pandas as pd
from ldap3 import Server, Connection, SIMPLE, SYNC, ALL
from werkzeug.datastructures import MultiDict
import config # Добавляем импорт config

# === Константы для LDAP аутентификации ===
LDAP_SERVER = 'ldap.ultrastar.ru' # Адрес LDAP сервера
LDAP_PORT = 389 # Порт LDAP сервера
LDAP_DN = 'dc=ultrastar,dc=ru' # Базовый DN (Distinguished Name)
LDAP_SEARCH_BASE = 'ou=users,dc=ultrastar,dc=ru'  # Базовый DN для поиска пользователей в LDAP

# === Функции валидации данных форм ===

# --- Валидация данных первой страницы (home_form) ---
# Проверяет обязательные поля и уникальность SAP-кода.
def home_verif(session):
    db = sqlite3.connect(config.DB_PATH) # Подключение к БД
    cursor = db.cursor()

    # Проверка и обновление SAP-кода, если он предоставлен
    if 'SAP_code' in session['home_form'] and session['home_form']['SAP_code']:
        sap_code = str(session['home_form']['SAP_code']).strip() # Удаление лишних пробелов
        # Проверка на существование такого SAP-кода в других записях
        cursor.execute('''
            SELECT COUNT(*) 
            FROM calculations 
            WHERE CAST(SAP_code AS TEXT) = ? 
            AND id != ?
        ''', (sap_code, session.get("id", -1))) # Используем session.get для случая нового расчета без id
        count = cursor.fetchone()[0]
        if count > 0:
            db.close()
            return "SAP код уже существует в базе данных"

        # Обновление SAP-кода в базе данных для текущего расчета (если id существует)
        if "id" in session:
            cursor.execute('''
                UPDATE calculations 
                SET SAP_code = ? 
                WHERE id = ?
            ''', (sap_code, session["id"]))
            db.commit()
    
    db.close() # Закрытие соединения с БД
    
    # Проверка на заполненность обязательных полей
    if not session['home_form']['field1'] or not session['home_form']['field2'] or not session['home_form']['field3']:
        return "Заполните все обязательные поля"

    return 0 # 0 означает успешную валидацию

# --- Валидация данных второй страницы (second_form) ---
# Комплексная проверка полей, связанных с производством, размерами и трафаретами.
def second_verif(form):
    # Проверка наличия и заполненности ключевых полей
    if ('Comp' in form) and ('prod' in form) and ('prev' in form) and ('Traf' in form):
        # Проверка заполненности размеров изделия
        if (form["width"] != "") and (form["width_num"] != "") and \
        (form["length"] != "") and (form["length_num"] != ""): 
            # Валидация данных, связанных с трафаретами
            if (form["Traf"] == "1"): # Если трафареты давальческие
                return 0 # Валидация успешна
            elif not ("sides_SMD" in form): # Если трафареты не давальческие, проверяем количество сторон
                return 'Заполните количество сторон' 
            elif not ("Trafs_costs_select" in form): # Проверка выбора способа оценки трафарета
                return 'Выберите способ оценки трафарета'
            elif form["Trafs_costs_select"] == "1": # Если выбрана тарифная опция
                return 0 # Валидация успешна
            elif "Traf_value" in form: # Если выбран ручной ввод стоимости трафарета
                if form["Traf_value"] != '': # Проверка, что поле стоимости заполнено
                    return 0 # Валидация успешна
                else:
                    return "Выберите стоимость трафарета"
            else: # Если не выбран ручной ввод, но и не тарифная опция (недостижимо при текущей логике HTML, но для полноты)
                 return "Некорректные данные по трафаретам"
        else:
            return 'Заполните размеры изделия' # Ошибка: не заполнены размеры
    else:
        return 'Заполните все поля' # Ошибка: не заполнены основные поля

# --- Валидация данных для SMD монтажа ---    
def smd_verif(session):
    # Проверка, что если выбрана опция SMD, то загружены таблицы BOM и PAP
    if "SMD" in session["SMD_form"]:
        if not ("tables" in session): # "tables" - ключ в сессии, куда сохраняются обработанные данные BOM/PAP
            return "Загрузите таблицу BOM и PAP"
    return 0 # Успешная валидация

# --- Валидация данных для страницы Тестирования ---
def test_verif(form):
    if "Test" in form: # Если активирована опция тестирования
        # Проверка, что итоговая стоимость не является NaN (Not a Number)
        if form["money_all_f"] == 'NaN руб':
            return "Заполните все поля"
    return 0 # Успешная валидация

# --- Валидация данных для страницы Отмывки ---
def clear_verif(form):
    if "Clear" in form: # Если активирована опция отмывки
        # Проверка, что итоговая стоимость не является Infinity (бесконечность)
        if form["money_all_f"] == 'Infinity руб':
            return "Заполните все поля"
    return 0 # Успешная валидация

# --- Валидация данных для страницы Разделения ---
def sep_verif(form):
    if "Sep" in form: # Если активирована опция разделения
        if form["money_all_f"] == 'NaN руб':
            return "Заполните все поля"
    return 0 # Успешная валидация

# --- Валидация данных для страницы Рентген-контроля ---
def xray_verif(form):
    if "Xray" in form: # Если активирована опция рентген-контроля
        if form["money_all_f"] == 'NaN руб':
            return "Заполните все поля"
    return 0 # Успешная валидация

# --- Валидация данных для страницы Ручной лакировки ---
def handv_verif(form):
    if "Handv" in form: # Если активирована опция ручной лакировки
        if form["money_all_f"] == 'NaN руб':
            return "Заполните все поля"
    return 0 # Успешная валидация

# === Функции сохранения и аутентификации ===

# --- Автоматическое сохранение данных сессии в БД --- 
# Сохраняет текущее состояние расчета в базу данных.
def auto_save(session):
    # Подготовка данных сессии для сохранения
    session_data_to_save = {} 
    # Формирование пути и имени файла для старой логики сохранения в pickle (сейчас не используется для записи)
    path_pickle = "Calculations/" + str(session["home_form"]["field1"]) + "/" + str(session["home_form"]["field2"])
    current_time = datetime.now()
    name_pickle = str(session["home_form"]["field1"]) + "_" + str(session["home_form"]["field2"]) + "_" + str(session["home_form"]["field3"]) + "_" + str(session["date"])
    if "comm" in session["home_form"] and session["home_form"]["comm"] != "":
        name_pickle += "_" + session["home_form"]["comm"]       
    
    # Копирование всех элементов сессии
    for key, value in session.items():
        session_data_to_save[key] = value
        
    # # Создание директории, если она не существует (для старой логики pickle)
    # if not os.path.exists(path_pickle):
    #     os.makedirs(path_pickle)
        
    session_data_to_save["check"] = 0 # Установка флага "check" в 0 (означает, что расчет не завершен/не скачан)
    
    # # Логика сохранения в pickle файл (закомментирована в пользу БД)
    # with open(path_pickle +"/" + name_pickle + '.pickle', 'wb') as file:
    #     pickle.dump(session_data_to_save, file)
    
    # Преобразование MultiDict в обычные словари для корректного сохранения в БД
    if 'home_form' in session_data_to_save and isinstance(session_data_to_save['home_form'], MultiDict):
        home_form_dict = dict(session_data_to_save['home_form'])
        # Обновляем session_data_to_save, преобразуя все MultiDict и добавляя поля из home_form напрямую
        session_data_final = {k: dict(v) if isinstance(v, MultiDict) else v for k, v in session_data_to_save.items()}
        session_data_final.update(home_form_dict)
    else: # Если home_form нет или уже словарь
        session_data_final = {k: dict(v) if isinstance(v, MultiDict) else v for k, v in session_data_to_save.items()}
        if 'home_form' in session_data_final and isinstance(session_data_final['home_form'], dict):
             session_data_final.update(session_data_final['home_form']) # Добавляем поля из home_form, если это уже словарь

    # Подключение к БД
    db = sqlite3.connect(config.DB_PATH)
    cursor = db.cursor()

    # cursor.execute('''
    #     ALTER TABLE calculations 
    #     ADD COLUMN contract INTEGER DEFAULT 0
    # ''')
    # cursor.execute('''
    #     ALTER TABLE calculations 
    #     ADD COLUMN SAP_code INTEGER
    # ''')
    # db.commit()
    
    # Формирование SQL-запроса на обновление
    # Ключи оборачиваются в двойные кавычки для совместимости с именами столбцов, содержащими пробелы или спецсимволы (хотя здесь это не актуально)
    update_columns_sql = ', '.join(f'"{key}" = ?' for key in session_data_final.keys())
    update_values = [str(value) for value in session_data_final.values()] # Все значения приводятся к строке для сохранения
            
    # Выполнение UPDATE запроса
    cursor.execute(
        f'''UPDATE calculations 
            SET {update_columns_sql}
            WHERE id = ?''',
        update_values + [session_data_final["id"]] # ID текущего расчета
    )
    db.commit() # Сохранение изменений в БД
    db.close() # Закрытие соединения

# --- Аутентификация пользователя по локальному CSV файлу (устаревшая) ---
# def log_in(form):
#     base = pd.read_csv('data/Rights.csv', header=None)
#     login = form["username"]
#     password = form["password"]
#     for row in base.iterrows():
#         if login == row[1][0]:
#             if password == row[1][1]:
#                 return row[0] # Возвращает ID или уровень доступа пользователя
#     return -1 # Ошибка аутентификации

# --- Аутентификация пользователя через LDAP --- 
# Пытается аутентифицировать пользователя на LDAP сервере и проверить его членство в группе 'money-contract'.
def authenticate(username_ldap, password_ldap):
#    return username_ldap
    try:
        server = Server(LDAP_SERVER, port=LDAP_PORT, get_info=ALL)
        # Формирование полного имени пользователя для LDAP (uid=username,dc=ultrastar,dc=ru)
        ldap_full_username = "uid=" + username_ldap + "," + LDAP_DN 
        
        # Попытка подключения и биндинга к LDAP серверу
        conn = Connection(server, auto_bind=True, user=ldap_full_username, password=password_ldap, authentication=SIMPLE, check_names=True)
        
        if conn.bind(): # Если биндинг успешен (учетные данные верны)
            # Проверка членства пользователя в группе 'money-contract'
            group_search_base = "ou=groups," + LDAP_DN  # База для поиска групп
            group_search_filter = '(cn=money-contract)' # Фильтр для поиска конкретной группы
            group_attributes = ["memberUid"] # Атрибут, содержащий членов группы

            conn.search(search_base=group_search_base, search_filter=group_search_filter, attributes=group_attributes)

            if conn.entries and conn.entries[0].memberUid: # Если группа найдена и у нее есть члены
                group_members = conn.entries[0].memberUid.values 
                if username_ldap in group_members: # Если пользователь является членом группы
                    conn.unbind()
                    return username_ldap # Аутентификация и авторизация успешны
                else: # Пользователь аутентифицирован, но не состоит в нужной группе
                    conn.unbind()
                    return -2 # Код ошибки: нет прав (не в группе)
            else: # Группа не найдена или не содержит членов (маловероятно, если группа существует)
                conn.unbind()
                # Можно вернуть -2 (нет прав) или -1 (общая ошибка), в зависимости от политики
                # Текущая логика основного файла main.py ожидает -2 для "нет прав".
                return 0
        else:
            # Ошибка биндинга (неправильные учетные данные)
            conn.unbind() # Явное освобождение соединения
            return -1 # Код ошибки: неверный логин/пароль
    except Exception as e:
        # Любая другая ошибка при подключении или работе с LDAP
        print(f"LDAP Authentication Error: {e}") # Для отладки
        return -1 # Общая ошибка аутентификации