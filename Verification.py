import pickle
from datetime import datetime
import os
import sqlite3
import pandas as pd
from ldap3 import Server, Connection, SIMPLE, SYNC, ALL
from werkzeug.datastructures import MultiDict

LDAP_SERVER = 'ldap.ultrastar.ru'
LDAP_PORT = 389
LDAP_DN = 'dc=ultrastar,dc=ru'
LDAP_SEARCH_BASE = 'ou=users,dc=ultrastar,dc=ru'  # Базовый DN для поиска пользователей


def home_verif(session):
    db = sqlite3.connect('Calculations/calculation.db')
    cursor = db.cursor()

    if 'SAP_code' in session['home_form'] and session['home_form']['SAP_code']:
        sap_code = str(session['home_form']['SAP_code']).strip()
        cursor.execute('''
            SELECT COUNT(*) 
            FROM calculations 
            WHERE CAST(SAP_code AS TEXT) = ? 
            AND id != ?
        ''', (sap_code, session["id"]))
        count = cursor.fetchone()[0]
        if count > 0:
            db.close()
            return "SAP код уже существует в базе данных"

        # Update SAP code in database
        cursor.execute('''
            UPDATE calculations 
            SET SAP_code = ? 
            WHERE id = ?
        ''', (sap_code, session["id"]))
        db.commit()
    
    db.close()
    
    if not session['home_form']['field1'] or not session['home_form']['field2'] or not session['home_form']['field3']:
        return "Заполните все обязательные поля"

    return 0

def second_verif(form):
    if ('Comp' in form) and ('prod' in form) and ('prev' in form) and ('Traf' in form): # Проверка, что поля "Комплектация", "Производство", "Производилось ли ранее", "Трафареты" заполнены
        if (form["width"] != "") and (form["width_num"] != "") and \
        (form["length"] != "") and (form["length_num"] != ""): # Проверка, что размеры заполнены
            # Остаётся только сложная проверка по трафаретам
            if (form["Traf"] == "1"): 
                return 0 #Если трафареты давальческие, то всё ок
            elif not ("sides_SMD" in form):
                return 'Заполните количество сторон' #Проверка, что заполнено количество сторон
            elif not ("Trafs_costs_select" in form):
                return 'Выберите способ оценки трафарета'
            elif form["Trafs_costs_select"] == "1":
                return 0 #Выбрана тарифная опция, всё ок
            elif "Traf_value" in form:
                if form["Traf_value"] != '': #Проверка, что в случае выбора поля для ручного заполнения оно не пустое
                    return 0
                else:
                    return "Выберите стоимость трафарета"
        else:
            return 'Заполните размеры изделия' # Не заполнены размеры
    else:
        return 'Заполните все поля'
    
def smd_verif(session):
    if "SMD" in session["SMD_form"]:#Проверка, что если стоит галочка, то была загружена таблица
        if not ("tables" in session):
            return "Загрузите таблицу BOM и PAP"
    return 0

def test_verif(form):
    if "Test" in form:
        if form["money_all_f"] == 'NaN руб':
            return "Заполните все поля"
    return 0

def clear_verif(form):
    if "Clear" in form:
        if form["money_all_f"] == 'Infinity руб':
            return "Заполните все поля"
    return 0

def sep_verif(form):
    if "Sep" in form:
        if form["money_all_f"] == 'NaN руб':
            return "Заполните все поля"
    return 0

def xray_verif(form):
    if "Xray" in form:
        if form["money_all_f"] == 'NaN руб':
            return "Заполните все поля"
    return 0

def handv_verif(form):
    if "Handv" in form:
        if form["money_all_f"] == 'NaN руб':
            return "Заполните все поля"
    return 0

def auto_save(session):
    session_data = {} 
    path = "Calculations/" + str(session["home_form"]["field1"]) + "/" + str(session["home_form"]["field2"])
    current_time = datetime.now()
    name = str(session["home_form"]["field1"]) + "_" + str(session["home_form"]["field2"]) + "_" + str(session["home_form"]["field3"]) + "_" + str(session["date"])
    if "comm" in session["home_form"]:
        if session["home_form"] != "":
            name += "_" + session["home_form"]["comm"]       
    for key, value in session.items():
        session_data[key] = value
    if not os.path.exists(path):
        os.makedirs(path)
    session["check"] = 0
    # with open(path +"/" + name + '.pickle', 'wb') as file:
    #     pickle.dump(session_data, file)
    
    home_form_data = dict(session_data['home_form'])
    session_data = {k: dict(v) if isinstance(v, MultiDict) else v for k, v in session_data.items()}  # Преобразуем все MultiDict в словари
    session_data.update(home_form_data)
    
    db = sqlite3.connect('Calculations/calculation.db')
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
    
    columns = ', '.join(f'"{key}" = ?' for key in session_data.keys())
    values = [str(value) for value in session_data.values()]
            
    cursor.execute(
        f'''UPDATE calculations 
            SET {columns}
            WHERE id = ?''',
        values + [session["id"]]
    )
    db.commit()


def log_in(form):
    base = pd.read_csv('data/Rights.csv', header=None)
    login = form["username"]
    password = form["password"]
    for row in base.iterrows():
        if login == row[1][0]:
            if password == row[1][1]:
                return row[0]
    return -1

def authenticate(username, password):
    try:
        server = Server(LDAP_SERVER, port=LDAP_PORT, get_info=ALL)
        user = username
        username = "uid=" + username + "," + LDAP_DN
        conn = Connection(server, auto_bind=True, user=username, password=password, authentication=SIMPLE, check_names=True)
        if conn.bind():
            # Аутентификация прошла успешно
                # Поиск пользователя
            search_base = "ou=groups," + LDAP_DN  # База поиска групп в соответствии с вашим сервером
            search_filter = '(cn=money-contract)'
            attributes = ["memberUid"]

            conn.search(LDAP_DN, search_filter, attributes=attributes)

            if conn.entries:
                group_members = conn.entries[0].memberUid.values  # Получаем список членов группы
                if user in group_members:
                    conn.unbind()
                    return user
            return user
        else:
            # Неправильные учетные данные
            return -1
    except Exception as e:
        # Ошибка аутентификации или подключения к серверу LDAP
        return -1