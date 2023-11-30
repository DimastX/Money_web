import pickle
from datetime import datetime
import os
import pandas as pd
from ldap3 import Server, Connection, SIMPLE, SYNC, ALL
LDAP_SERVER = 'ldap.ultrastar.ru'
LDAP_PORT = 389
LDAP_DN = 'dc=ultrastar,dc=ru'
LDAP_SEARCH_BASE = 'ou=users,dc=ultrastar,dc=ru'  # Базовый DN для поиска пользователей


def home_verif(form):
    if (form['field1'] != "") and (form['field2'] != "") and (form['field3'] != ""): # Проверка, что на первой странице заполнены все поля
        return 0
    return 'Заполните все поля'

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
    name = str(session["home_form"]["field1"]) + "_" + str(session["home_form"]["field2"]) + "_" + str(session["home_form"]["field3"]) + "_" + str(current_time.year) + "-" + str(current_time.month) + "-" + str(current_time.day)
    if "comm" in session["home_form"]:
        if session["home_form"] != "":
            name += "_" + session["home_form"]["comm"]       
    for key, value in session.items():
        session_data[key] = value
    if not os.path.exists(path):
            os.makedirs(path)
    with open(path +"/" + name + '.pickle', 'wb') as file:
        pickle.dump(session_data, file)

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