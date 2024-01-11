from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, Response, jsonify, g
from functools import wraps
from flask_table import Table, Col
import pandas as pd
import calculations_money as cm
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename
import tables as tb
import directories
import pickle
import Verification as ver
from flask_ldap3_login import LDAP3LoginManager

import time

from datetime import datetime
import os

import logging

# Настройка логирования
logging.basicConfig(filename='mylog.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
#Проверка
app = Flask(__name__)
app.secret_key = 'your_secret_key'
password = '1234' # Пароль для редактирования констант
Calculations_path = "Calculations/" # Путь хранения расчётов
actual_version = "1.0"
""" Функция для загрузки тарифов из таблицы .csv"""
def readdata():
    return pd.read_csv('data/tarifs.csv')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        return redirect(url_for('login_post'))
    return decorated_function

def clear_session():
    user = ""
    if "logged_in" in session:
        user = session["logged_in"]
    session.clear()
    if user != "":
        session["logged_in"] = user

"""Стартовая страница"""
@app.route('/', methods=['GET', 'POST'])
@login_required
def start():
    if request.method == 'POST':
        # Очистка cookies и открытие формы расчёта
        if 'next' in request.form:
            clear_session()
            return redirect(url_for('home'))
        # Открытие каталога изделий
        if 'dirs' in request.form:
            return redirect(url_for('list_directories'))
    return render_template('Start.html') #Открытие стартовой станицы


@app.route('/login2', methods=['GET'])
def index():
    return render_template('login2.html')

@app.route('/Dirs2', methods=['GET'])
def list_directories():
    program_directory = os.path.dirname(os.path.abspath(__file__)) + "\Calculations"
    selected_path = request.args.get('path', program_directory)
    items = os.listdir(selected_path)
    #Доступ только к расчётам
    if not selected_path.startswith(program_directory):
        return redirect(url_for('start'))
    if selected_path != '/':
        # Получаем путь к родительской папке
        parent_directory = os.path.dirname(selected_path)
    else:
        # Если текущий путь является корневым, то путь к родительской папке также /
        parent_directory = '/'
        
    parent_relative_path = os.path.relpath(selected_path, program_directory)
    if parent_relative_path == "..":
        return redirect(url_for('start'))
    dir_exists = False
    for item in items:
        if os.path.isdir(os.path.join(selected_path, item)):
            dir_exists = True
            break
    if dir_exists:
        return render_template('Dirsonly.html', items=items, os=os, program_directory=program_directory, 
                               selected_path=selected_path, parent_directory=parent_directory)
    else:
        file_data = []
        for item in items:
            file_path = os.path.join(selected_path, item)
            if not os.path.isdir(file_path):
                file_name, file_extension = os.path.splitext(item)
                if file_extension == ".pickle":
                    visible = 1
                    edit = 1
                    with open(file_path, 'rb') as file:
                        session_data = pickle.load(file)
                        if ("home_form" in session_data):
                            if ("contract" in session_data["home_form"]):
                                edit = 0
                        if ("version" in session_data) and ("check" in session_data):
                            if session_data["version"] == actual_version:
                                if (session_data["check"] == 1) or (edit == 0):
                                    if os.path.isfile(selected_path+"\\"+file_name+".xlsx"):
                                        visible = 0
                    words = file_name.split("_")
                    file_data.append({
                        'name': words[1] if words else '',
                        'batch_size': words[2] if len(words) > 2 else '',
                        'date': words[3] if len(words) > 3 else '',
                        'comment': words[4] if len(words) > 4 else '',
                        'file_path': file_path,
                        'visibility_download': visible,
                        'visibility_edit': edit
                    })
                    

    return render_template('Dirs4.html', file_data=file_data, dir_exists=dir_exists, selected_path=selected_path, os=os,
                           parent_directory=parent_directory)

@app.route('/copy', methods=['POST'])
def copy_file():
    with open(request.form["file_path"], 'rb') as file:
        session_data = pickle.load(file)
        session.update(session_data) # Задание в значение session данных из предыдущего расчёта
        session.pop('date', None) 
    return redirect(url_for('home'))

@app.route('/open', methods=['POST'])
def open_file():
    with open(request.form["file_path"], 'rb') as file:
        session_data = pickle.load(file)
        session.update(session_data) # Задание в значение session данных из предыдущего расчёта
    return redirect(url_for('home'))

@app.route('/download', methods=['POST'])
def download_file():
    file_path = request.form["file_path"]
    file_path = file_path.split(".")[0] + ".xlsx"
    with open(file_path, 'rb') as file:
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='text/csv', as_attachment=True) # Скачивание файла
    return redirect(url_for('home'))

@app.route('/login3', methods=['POST'])
def login3():
    username = request.form['username']
    password = request.form['password']

    if ver.authenticate(username, password):
        # Аутентификация прошла успешно
        return 'Успешная аутентификация'
    else:
        # Неправильные учетные данные
        return 'Неправильное имя пользователя или пароль'
    return render_template('login2.html')
    

@app.route('/login', methods=['GET', 'POST'])
def login_post():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = ver.authenticate(username, password)
        if user == -1:
            flash("Неверный логин или пароль")
        elif user == -2:
            flash("У вас нет прав")
        else:
            session['logged_in'] = user
            return redirect(url_for("start"))
    return render_template('login.html') #Открытие стартовой станицы

"""Страница с каталогом изделий"""
@app.route('/dirs', methods=['GET', 'POST'])
@login_required
def dirs():
    file_tree = directories.generate_file_tree('Calculations')  # Путь к директории с заказчиками

    clear_session()
    if request.method == 'POST':
        if 'prev' in request.form:
            return redirect(url_for('start'))
        if 'open' in request.form:
            # Путь к файлу вида: Директория_хранения/Имя_заказчика/Наименование_изделия/Название_расчёта.pickle
            file_path = Calculations_path + request.form['parent_folder'] + "/" + request.form['child_folder'] + "/" + request.form['sub_folder'] + ".pickle"
            # Открытие файла полученному по этому пути
            with open(file_path, 'rb') as file:
                session_data = pickle.load(file)
                session.update(session_data) # Задание в значение session данных из предыдущего расчёта
            return redirect(url_for('home'))
        if 'download' in request.form:
            # Путь к файлу вида: Директория_хранения/Имя_заказчика/Наименование_изделия/Название_расчёта.csv
            file_path = Calculations_path + request.form['parent_folder'] + "/" + request.form['child_folder'] + "/" + request.form['sub_folder']
            if os.path.exists(file_path + ".csv") or os.path.exists(file_path + ".xlsx"):
                with open(file_path + ".pickle", 'rb') as file:
                    session_data = pickle.load(file)
                    session.update(session_data)
                if "check" not in session:
                    flash("Расчёт был сделан в старой версии приложения. Убедитесь в его актуальности. Откройте изделие и скачайте расчёт оттуда")
                    return render_template('Dirs.html', file_tree=file_tree)
                elif session["check"] == 0:
                    flash("Расчёт был недоделан, либо были внесены изменения, актуализируйте его")
                    return redirect(url_for('home'))
                if os.path.exists(file_path + ".xlsx"):
                    return send_file(file_path + ".xlsx", mimetype='text/csv', as_attachment=True) # Скачивание файла
                if os.path.exists(file_path + ".csv"):
                    return send_file(file_path + ".csv", mimetype='text/csv', as_attachment=True) # Скачивание файла ``
            else:
                flash("Расчёт на такой файл ещё не был создан")
    return render_template('Dirs.html', file_tree=file_tree)


"""Создание списка всех заказчиков"""
@app.route("/get_child_folders", methods=["POST"])
def get_child_folders():
    parent_folder = request.form["parent_folder"]
    session["dirs1"] = parent_folder # Запись значения имени заказчика в session
    path = Calculations_path+str(parent_folder)
    child_folders = directories.generate_file_tree(path)
    return jsonify({"child_folders": child_folders})


""" Создание списка всех изделий"""
@app.route("/get_sub_folders", methods=["POST"])
def get_sub_folders():
    path = Calculations_path + session['dirs1'] + "/" + str(request.form["child_folder"])
    session["dirs2"] = str(request.form["child_folder"])# Запись значения названия изделия в session
    sub_folders = directories.generate_file_tree2(path)
    return jsonify({"sub_folders": sub_folders})


""" Страница с созданием нового заказчика """
@app.route("/new_customer", methods=['GET', 'POST'])
def cust():
    if request.method == 'POST':
        if 'new' in request.form:
            folder_name = request.form["name"] # Получение имени нового заказчика
            folder_path = Calculations_path + folder_name
            if not os.path.exists(folder_path): #Если такого имени ещё нет то создаётся новая директория
                os.makedirs(folder_path)
            return redirect(url_for("home"))
    return render_template('Cust.html')


"""Первая страница с информацией по изделию"""
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    msg = ""
    file_tree = directories.generate_file_tree('Calculations') # Создание списка всех заказчиков
    if not "date" in session:
        current_time = datetime.now()
        session["date"] = str(current_time.year) + "-" + str(current_time.month) + "-" + str(current_time.day)
    if request.method == 'POST':
        session['home_form'] = request.form # Сохранение всех полей в случае отправки формы
        if 'back' in request.form:
            return redirect(url_for('start')) # Возвращение на предыдущую страницу
        if 'tariffs' in request.form:
            session['last_page'] = 'home' # Запоминание страницы с которой уходим, для дальнейшего возвращения на неё
            return redirect(url_for('tariffs')) # Открытие страницы с тарифами
        if 'new' in request.form:
            return redirect(url_for('cust')) # Открытие страницы с созданием нового заказчика
        if 'next' in request.form:
            msg = ver.home_verif(session["home_form"]) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                return redirect(url_for('second')) #Переход на вторую страницу
            else:
                flash(msg) # Вывод всплывающего уведомления о некорректном заполнении
    return render_template('home.html', file_tree=file_tree)


"""Страница с информацией по производству изделия"""
@app.route('/second', methods=['GET', 'POST'])
@login_required
def second():
    msg = ""
    if request.method == 'POST':
        session['second_form'] = request.form # Сохранение всех полей в случае отправки формы
        ver.auto_save(session)
        if 'tariffs' in request.form:
            session['last_page'] = 'second'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('home'))
        if 'next' in request.form:
            msg = ver.second_verif(session["second_form"]) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                return redirect(url_for('smd')) #Переход на вторую страницу
            else:
                flash(msg) # Вывод всплывающего уведомления о некорректном заполнении
    return render_template('second.html')

"""Страница с тарифами"""
@app.route('/tariffs', methods=['GET', 'POST'])
@login_required
def tariffs():
    df = readdata()
    if request.method == 'POST':
        session['tariffs_form'] = request.form 
        if 'back' in request.form:
            return redirect(url_for(session['last_page']))
        elif 'check' in request.form:
            if request.form['password'] == password:
                return redirect(url_for('edittable'))
            else:
                msg = 'Неправильный пароль'
                flash(msg)
    return render_template('tariffs.html', tables=[df.to_html(classes='table', index=False, header="true")])


"""редактируемая страница с тарифами"""
@app.route('/edittable', methods=['POST', 'GET'])
@login_required
def edittable():
    df = readdata()
    # Если это POST-запрос с данными для обновления таблицы
    if request.method == 'POST':
        # Извлекаем данные из формы и обновляем ячейки во 2-м столбце
        if 'save' in request.form:
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Стоимость, руб/ч"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/tarifs.csv', index=False)
            # Сохраняем обновленный dfв
            return redirect(url_for('tariffs'))
    return render_template('edittable.html', df = df, tables=[df.to_html(classes='table', index=False, header="true")])

"""Страница с смд монтажом"""
@app.route('/SMD', methods=['GET', 'POST'])
@login_required
def smd():
    edit = "0"
    edit2 = "0"
    df = pd.read_csv('data/SMD.csv') #Константы СМД линии
    df2 = readdata()
    df3 = pd.read_csv('data/SMD2.csv').values.tolist() #Скорость монтажа на смд линии для удобной обработки в JS
    df4 = pd.read_csv('data/SMD2.csv') #Скорость монтажа на смд линии
    if "tables" in session:
        if session["tables"] == 0: #Если ошибка 0, т.е в РАР не 2 разных позиции
            flash("PAP файл заполнен некорректно. Неправильно введён столбец Layer")
    if request.method == 'POST': 
        session['SMD_form'] = request.form
        session['tables'] = [int(session['SMD_form']["SMD1"]),
                             int(session['SMD_form']["SMD2"]),
                             int(session['SMD_form']["SMD3"]),
                             int(session['SMD_form']["SMD4"]),
                             int(session['SMD_form']["SMD5"])]
        ver.auto_save(session)
        if 'tariffs' in request.form:
            session['last_page'] = 'smd'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('second'))
        if 'next' in request.form:
            msg = ver.smd_verif(session) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                return redirect(url_for('comp')) #Переход на следующую страницу
            else:
                flash(msg) # Вывод всплывающего уведомления о некорректном заполнении
        if 'save' in request.form: #Проверка, что подходит пароль для первой таблицы
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save2' in request.form: #Изменение второй таблицы
            tb.update_table("SMD", request.form, df)
        if 'save3' in request.form: #Проверка, что подоходит пароль для второй таблицы
            if request.form['password2'] == password:
                edit2 = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save4' in request.form: #изменение второй таблицы
            tb.update_table2("SMD2", request.form, df4)
        if 'template' in request.form:
            return send_file('Documentation/Template.xls', as_attachment=True)
    return render_template('SMD.html', df=df, df2=df2, edit=edit, df3=df3, edit2=edit2, df4=df4)

"""Функция обработки вызванной таблицы"""
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    file = request.files['csv_file']
    if file:
        tables = tb.tables(file)
        if tables == 0:
            session['tables'] = 0
        else: 
            session['tables']= tables #Запись данных обработки таблицы BOM и PAP
        return redirect(url_for('smd'))
    else:
        return 'Файл не был загружен'
    
"""Страница с комплектацией"""
@app.route('/Comp', methods=['GET', 'POST'])
@login_required
def comp():
    edit = "0"
    df = pd.read_csv('data/Comp.csv') #Константы СМД линии
    df2 = readdata()
    if request.method == 'POST':
        session['Comp_form'] = request.form
        ver.auto_save(session)
        if 'tariffs' in request.form:
            session['last_page'] = 'comp'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('smd'))
        if 'next' in request.form:
            return redirect(url_for('tht'))
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save2' in request.form:
            tb.update_table("THT", request.form, df)
    return render_template('Comp.html', df=df, df2=df2, edit=edit)
    
"""THT монтаж"""
@app.route('/THT', methods=['GET', 'POST'])
@login_required
def tht():
    edit = "0"
    df = pd.read_csv('data/THT.csv') #Константы ТНТ монтажа
    df2 = readdata()
    if request.method == 'POST':
        session['THT_form'] = request.form
        ver.auto_save(session)
        if 'tariffs' in request.form:
            session['last_page'] = 'tht'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('comp'))
        if 'next' in request.form:
            return redirect(url_for('wave'))
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save2' in request.form:
            tb.update_table("THT", request.form, df)
    return render_template('THT.html', df=df, df2=df2, edit=edit)


"""Волновая пайка"""
@app.route('/wave', methods=['GET', 'POST'])
@login_required
def wave():
    edit = "0"
    df = pd.read_csv('data/Wave.csv')
    df2 = readdata()
    if request.method == 'POST':
        session['Wave_form'] = request.form
        ver.auto_save(session)
        if 'tariffs' in request.form:
            session['last_page'] = 'wave'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('tht'))
        if 'next' in request.form:
            return redirect(url_for('HRL'))
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save2' in request.form:
            tb.update_table("Wave", request.form, df)
    return render_template('Wave.html', df=df, df2=df2, edit=edit)

"""Лакировка HRL"""
@app.route('/HRL', methods=['GET', 'POST'])
@login_required
def HRL():
    edit = "0"
    df = pd.read_csv('data/HRL.csv')
    df2 = readdata()
    if request.method == 'POST':
        session['HRL_form'] = request.form
        ver.auto_save(session)
        if 'tariffs' in request.form:
            session['last_page'] = 'HRL'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('wave'))
        if 'next' in request.form:
            return redirect(url_for('hand'))
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save2' in request.form:
            tb.update_table("HRL", request.form, df)
    return render_template('HRL.html', df=df, df2=df2, edit=edit)

"""Ручной монтаж"""
@app.route('/hand', methods=['GET', 'POST'])
@login_required
def hand():    
    edit = "0"
    df = pd.read_csv('data/Hand.csv')
    df2 = readdata()
    if request.method == 'POST':
        session['Hand_form'] = request.form
        ver.auto_save(session)
        if 'tariffs' in request.form:
            session['last_page'] = 'hand'
            return redirect(url_for('tariffs'))
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'back' in request.form:
            return redirect(url_for('HRL'))   
        if 'save2' in request.form:
            tb.update_table("Hand", request.form, df)
        if 'next' in request.form:
                return redirect(url_for('test'))
    return render_template('Hand.html', df=df, df2=df2, edit=edit)


"""Тестирование"""
@app.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    edit = "0"
    df2 = readdata()
    df = pd.read_csv('data/Test.csv')
    rows = 0
    if request.method == 'POST': 
        session['Test_form'] = request.form
        ver.auto_save(session)
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save2' in request.form: 
            tb.update_table("Test", request.form, df)
        if 'tariffs' in request.form:
            session['last_page'] = 'test'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('hand'))
        if 'next' in request.form:
            msg = ver.test_verif(request.form) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                return redirect(url_for('clear')) #Переход на следующую страницу
            else:
                flash(msg) # Вывод всплывающего уведомления о некорректном заполнении
    return render_template('Test.html', df=df, df2=df2, edit=edit, rows=rows)


"""Отмывка"""
@app.route('/clear', methods=['GET', 'POST'])
@login_required
def clear():
    edit = "0"
    df = pd.read_csv('data/Clear.csv')
    df2 = readdata()
    data = cm.clear_calculations(session, df) #
    if request.method == 'POST':
        session['Clear_form'] = request.form
        ver.auto_save(session)
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'tariffs' in request.form:
            session['last_page'] = 'clear'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('test'))
        if 'save2' in request.form:
            tb.update_table("Clear", request.form, df)
        if 'next' in request.form:
            msg = ver.clear_verif(request.form) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                return redirect(url_for('handv')) #Переход на следующую страницу
            else:
                flash(msg) # Вывод всплывающего уведомления о некорректном заполнении
    return render_template('Clear.html', df = df, edit=edit, data=data, df2=df2)


"""Ручная лакировка"""
@app.route('/Handv', methods=['GET', 'POST'])
@login_required
def handv():
    edit = "0"
    df = pd.read_csv('data/Handv.csv')
    df2 = readdata()
    if request.method == 'POST':
        session['Handv_form'] = request.form
        ver.auto_save(session)
        if 'tariffs' in request.form:
            session['last_page'] = 'handv'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('clear'))
        if 'next' in request.form:
            msg = ver.handv_verif(request.form) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                return redirect(url_for('sep'))
            else:
                flash(msg) # Вывод всплывающего уведомления о некорректном заполнении
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save2' in request.form:
            tb.update_table("Handv", request.form, df)
    return render_template('Handv.html', df=df, df2=df2, edit=edit)


"""Разделение"""
@app.route('/separation', methods=['GET', 'POST'])
@login_required
def sep():
    df = pd.read_csv('data/Sep.csv')
    df2 = readdata()
    fields = 0
    edit = "0"
    time = cm.sep_calculations(session, df)
    if request.method == 'POST':
        session['Sep_form'] = request.form
        ver.auto_save(session)
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'tariffs' in request.form:
            session['last_page'] = 'sep'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('handv'))
        if 'save2' in request.form:
            tb.update_table("Sep", request.form, df)
        if 'next' in request.form:
            msg = ver.sep_verif(request.form) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                return redirect(url_for('xray')) #Переход на следующую страницу
            else:
                flash(msg) # Вывод всплывающего уведомления о некорректном заполнении
    return render_template('Sep.html', df=df, edit=edit, time=time, df2=df2)


"""Рентгенконтроль"""
@app.route('/xray', methods=['GET', 'POST'])
@login_required
def xray():
    fields = 0
    edit = "0"
    df2 = readdata()
    df = pd.read_csv('data/Xray.csv')
    if request.method == 'POST':
        session['Xray_form'] = request.form
        ver.auto_save(session)
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'tariffs' in request.form:
            session['last_page'] = 'xray'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('sep'))
        if 'save2' in request.form:
            tb.update_table("Xray", request.form, df)
        if 'next' in request.form:
            msg = ver.xray_verif(request.form) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                return redirect(url_for('pack')) #Переход на следующую страницу
            else:
                flash(msg) # Вывод всплывающего уведомления о некорректном заполнении
    return render_template('Xray.html', df=df, df2=df2, edit=edit)

@app.route('/pack', methods = ['GET', 'POST'])
@login_required
def pack():
    df = pd.read_csv('data/Pack.csv')
    df2 = readdata()
    fields = 0
    edit = "0"
    if request.method == 'POST':
        session['Pack_form'] = request.form
        ver.auto_save(session)
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'tariffs' in request.form:
            session['last_page'] = 'pack'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('xray'))
        if 'save2' in request.form:
            tb.update_table("Pack", request.form, df)
        if 'next' in request.form:
            msg = ver.xray_verif(request.form) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                return redirect(url_for('add')) #Переход на следующую страницу
            else:
                flash(msg) # Вывод всплывающего уведомления о некорректном заполнении
    return render_template('Pack.html', df=df, df2=df2, edit=edit)

"""Дополнительные работы"""
@app.route('/additional', methods=['GET', 'POST'])
@login_required
def add():
    fields = 0
    df2 = readdata()
    if request.method == 'POST':
        session['Add_form'] = request.form
        ver.auto_save(session)
        if 'tariffs' in request.form:
            session['last_page'] = 'add'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('pack'))
        if 'next' in request.form:
            return redirect(url_for('info'))
    return render_template('Add.html', df2=df2)


"""Страница с дополнительными затратами: прибыль + НДС"""
@app.route('/info', methods=['GET', 'POST'])
@login_required
def info():
    edit = "0"
    df2 = readdata()
    df = pd.read_csv('data/Info.csv')
    if request.method == 'POST':
        session['Info_form'] = request.form
        ver.auto_save(session)
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save2' in request.form:
            tb.update_table("Info", request.form, df)
        if 'next' in request.form:
            return redirect(url_for('session_data'))
        if 'back' in request.form:
            return redirect(url_for('add'))
        if 'tariffs' in request.form:
            session['last_page'] = 'info'
            return redirect(url_for('tariffs'))
    return render_template('Info.html', df=df, edit=edit, df2=df2)


"""Финальная таблица экспорта"""
@app.route('/session_data', methods=['GET', 'POST'])
@login_required
def session_data():
    df = cm.create_export(session) #Создание таблицы со всеми данными
    if isinstance(df[1], int):
        table = 0
    else:
        table = 1
    session['version'] = actual_version
    if request.method == 'POST':
        session["session_data"] = request.form
        if 'download' in request.form:
            session['check'] = 1
            current_time = datetime.now()
            path = "Calculations/" + str(session["home_form"]["field1"]) + "/" + str(session["home_form"]["field2"])
            name = str(session["home_form"]["field1"]) + "_" + str(session["home_form"]["field2"]) + "_" + str(session["home_form"]["field3"]) + "_" + str(session["date"])
            if "comm" in session["home_form"]:
                if session["home_form"] != "":
                    name += "_" + session["home_form"]["comm"]
            if not os.path.exists(path):
                os.makedirs(path)

            with pd.ExcelWriter(path +"/" + name + ".xlsx", engine='xlsxwriter') as writer:

                sheet_name = 'Трудозатраты'
                df_info = pd.DataFrame([["Заказчик", session['home_form']['field1']], ["Изделие", session['home_form']['field2']], ["Партия", session['home_form']['field3']]])
                df_info.to_excel(writer, index=False, sheet_name=sheet_name, header = False)
                #df1 = pd.concat([df[0], df[1]], keys=['Стоимость подготовки производства', 'Стоимость производства'])
                start_row = df_info.shape[0] + 2
                df[0].to_excel(writer, sheet_name=sheet_name, startrow= start_row, index=True)
                

                workbook = writer.book
                worksheet = writer.sheets['Трудозатраты']
                wrap_format = workbook.add_format({'text_wrap': True})
                # Создаем формат с обрамлением
                border_format = workbook.add_format({'border': 1})

                # Применяем формат к каждой ячейке в DataFrame информации о заказе
                for row_num, values in enumerate(df_info.values):
                    for col_num, value in enumerate(values):
                        worksheet.write(row_num, col_num, value, border_format)

                # Создаем формат с автоматическим переносом строки
                wrap_format = workbook.add_format({'text_wrap': True})

                # Применяем формат к каждой ячейке в основной таблице df[0]
                start_row += 1  # Переходим на первую строку с данными основной таблицы
                for row_num, values in enumerate(df[0].values):
                    for col_num, value in enumerate(values):
                        worksheet.write(row_num + start_row, col_num + 1, value, border_format)
                
                    
                # Применяем формат к каждой ячейке в дополнительной таблице df[1]
                if table:
                    start_row += df[0].shape[0] + 2  # Переходим на первую строку с данными дополнительной таблицы
                    for row_num, values in enumerate(df[1].values):
                        for col_num, value in enumerate(values):
                            worksheet.write(row_num + start_row, col_num, value, border_format)

                # Настройка ширины столбцов
                worksheet.set_column(0, 0, 45)  # Ширина первого столбца
                for col_num, column in enumerate(df[0].columns):
                    column_length = max(df[0][column].astype(str).map(len).max(), len(column))
                    worksheet.set_column(col_num + 1, col_num + 1, column_length + 1, wrap_format)
                worksheet.set_landscape()

                sheet_name = "Информация"
                df_info.to_excel(writer, index=False, sheet_name=sheet_name, header=False)

                # Записываем данные df[2] в файл Excel
                start_row = df_info.shape[0] + 2
                df[2].to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False)

                # Получаем объект workbook и worksheet из объекта writer
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]

                # Устанавливаем альбомную ориентацию страницы
                worksheet.set_landscape()

                # Создаем формат с обрамлением
                border_format = workbook.add_format({'border': 1})

                # Применяем формат к каждой ячейке в DataFrame информации
                for row_num, values in enumerate(df_info.values):
                    for col_num, value in enumerate(values):
                        worksheet.write(row_num, col_num, value, border_format)

                # Применяем формат к каждой ячейке в данных df[2]
                start_row += 1
                for row_num, values in enumerate(df[2].values):
                    for col_num, value in enumerate(values):
                        worksheet.write(row_num + start_row, col_num, value, border_format)

                # Настройка ширины столбцов
                worksheet.set_column(0, 0, 40)
                for col_num, column in enumerate(df[2].columns):
                    column_length = max(df[2][column].astype(str).map(len).max(), len(column))
                    worksheet.set_column(col_num + 1, col_num + 1, column_length + 1)
            session_data = {}
            for key, value in session.items():
                session_data[key] = value
            with open(path +"/" + name + '.pickle', 'wb') as file:
                pickle.dump(session_data, file)
            return send_file(path +"/" + name + ".xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True)
    if 'back' in request.form:
        session['check'] = 0
        return redirect(url_for('info'))
    if 'tariffs' in request.form:
        session['last_page'] = 'session_data'
        return redirect(url_for('tariffs'))
    if 'new' in request.form:
        clear_session()
        return redirect(url_for('home'))
    if table:
        return render_template('session_data.html', tables1=[df[0].to_html(classes='table', index=True, header="true")], table=table,
                           tables2=[df[1].to_html(classes='table', index=False, header="true")], 
                           tables3=[df[2].to_html(classes='table', index=False, header="true")])
    return render_template('session_data.html', tables1=[df[0].to_html(classes='table', index=True, header="true")], table = table,
                           tables3=[df[2].to_html(classes='table', index=False, header="true")])


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    #serve(app, host="0.0.0.0", port=5000)