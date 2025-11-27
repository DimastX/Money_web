from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, Response, jsonify, g, send_from_directory
from functools import wraps
import pandas as pd
import calculations_money as cm
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename
import tables as tb
import directories
import pickle
import Verification as ver
from flask_ldap3_login import LDAP3LoginManager
import sqlite3
import config # Добавляем импорт config

from datetime import datetime
import os

import logging

from RM_checklist.checklist_blueprint import checklist_bp

# === Инициализация Flask приложения и глобальные переменные ===
# Настройка логирования
logging.basicConfig(filename='mylog.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
#Проверка
app = Flask(__name__)
app.secret_key = 'your_secret_key'
password = '1234' # Пароль для редактирования констант
Calculations_path = "Calculations/" # Путь хранения расчётов
actual_version = "1.0"

# Определение путей в начале файла (после импортов)
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_PATH = os.path.join(BASE_DIR, 'Calculations', 'calculation.db')

# === Вспомогательные функции ===
""" Функция для загрузки тарифов из таблицы .csv"""
def readdata():
    """
    Загружает данные о тарифах из CSV-файла 'data/tarifs.csv'.

    Возвращает:
        pandas.DataFrame: Таблица с тарифами.
    """
    return pd.read_csv('data/tarifs.csv')

    
def get_db():
    """
    Открывает новое соединение с базой данных SQLite, если оно еще не открыто
    для текущего контекста приложения, или возвращает существующее.

    Соединение хранится в `flask.g` для повторного использования в рамках одного запроса.
    Путь к файлу БД берется из `config.DB_PATH`.
    Закрытие соединения обрабатывается функцией, декорированной `app.teardown_appcontext`.

    Возвращает:
        sqlite3.Connection: Объект соединения с базой данных.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(config.DB_PATH) # Используем config.DB_PATH
    return db

def login_required(f):
    """
    Декоратор для ограничения доступа к маршрутам только для аутентифицированных пользователей.

    Если пользователь не аутентифицирован (т.е. ключ 'logged_in' отсутствует
    в сессии), он будет перенаправлен на страницу входа ('login_post').

    Args:
        f (function): Функция представления (view function), которую нужно защитить.

    Returns:
        function: Обернутая функция представления.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        return redirect(url_for('login_post'))
    return decorated_function

def clear_session():
    """
    Очищает данные текущего расчета из сессии пользователя.

    Сохраняет информацию о залогиненном пользователе (`session["logged_in"]`),
    удаляя все остальные данные из сессии. Используется для подготовки
    к новому расчету или при переключении контекста.
    """
    user = ""
    if "logged_in" in session:
        user = session["logged_in"]
    session.clear()
    if user != "":
        session["logged_in"] = user

# === Маршруты приложения ===

# --- Стартовая страница ---
"""Стартовая страница"""
@app.route('/', methods=['GET', 'POST'])
@login_required
def start():
    """
    Стартовая страница приложения (главная страница после входа).

    Назначение:
    Предоставляет пользователю начальные опции: создать новый расчет
    или перейти к каталогу существующих расчетов.

    Методы HTTP:
    - GET: Отображает стартовую страницу.
    - POST: Обрабатывает выбор пользователя (создать новый расчет или открыть каталог).

    Декораторы:
    - @app.route('/', methods=['GET', 'POST']): Регистрирует эту функцию как обработчик
      для корневого URL ('/') и разрешает методы GET и POST.
    - @login_required: Гарантирует, что доступ к этой странице имеют только
      аутентифицированные пользователи. Если пользователь не вошел в систему,
      он будет перенаправлен на страницу входа.

    Логика GET-запроса:
    - Просто отображает HTML-шаблон 'Start.html'.

    Логика POST-запроса:
    - Проверяет, какая кнопка была нажата на форме в 'Start.html':
        - Если в `request.form` присутствует ключ 'next' (например, кнопка "Создать новый расчет"):
            1. Вызывается функция `clear_session()` для очистки данных предыдущего расчета
               из сессии (сохраняя при этом информацию о залогиненном пользователе).
            2. Пользователь перенаправляется на страницу создания нового расчета (маршрут 'home').
        - Если в `request.form` присутствует ключ 'dirs' (например, кнопка "Открыть каталог изделий"):
            1. Вызывается функция `clear_session()`.
            2. Пользователь перенаправляется на страницу выбора существующего расчета
               из базы данных (маршрут 'select_calculation').

    Входные данные (для POST):
    - `request.form`: Словарь, содержащий данные отправленной формы.
        - `request.form['next']`: Если была нажата кнопка, соответствующая созданию нового расчета.
        - `request.form['dirs']`: Если была нажата кнопка, соответствующая переходу в каталог.

    Выходные данные:
    - Для GET-запроса: Результат вызова `render_template('Start.html')`, т.е. HTML-страница.
    - Для POST-запроса: Результат вызова `redirect()` на соответствующий URL
      (`url_for('home')` или `url_for('select_calculation')`).

    Связанные шаблоны:
    - `templates/Start.html`: HTML-шаблон для этой страницы.

    Побочные эффекты:
    - При POST-запросе вызывается `clear_session()`, которая модифицирует объект `session`.
    """
    if request.method == 'POST':
        # Очистка cookies и открытие формы расчёта
        if 'next' in request.form:
            clear_session()
            return redirect(url_for('home'))
        # Открытие каталога изделий
        if 'dirs' in request.form:
            clear_session()
            return redirect(url_for('select_calculation'))
    return render_template('Start.html') #Открытие стартовой станицы

# --- Альтернативная страница входа (GET) неактуально---
@app.route('/login2', methods=['GET'])
def index():
    """
    Отображает альтернативную страницу входа в систему (login2.html).

    Маршрут: GET /login2
    Примечание: Обработка POST-запроса для этой формы логина
    осуществляется функцией `login3()`.
    """
    return render_template('login2.html')
 
# --- Выбор существующего расчета из БД ---
@app.route('/select_calculation', methods=['GET', 'POST'])
@login_required
def select_calculation():
    logging.basicConfig(filename='app.log', level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.debug("Request form data: %s", request.form)

    db = sqlite3.connect(config.DB_PATH) # Используем config.DB_PATH
    cursor = db.cursor()
    
    if request.method == 'POST':
        if 'customer' in request.form:
            customer = request.form['customer']
            cursor.execute('SELECT DISTINCT field2 FROM calculations WHERE field1 = ? ORDER BY field2', (customer,))
            products = cursor.fetchall()
            return jsonify({'products': [p[0] for p in products if p[0]]})
            
        elif 'product' in request.form:
            customer = request.form['selected_customer']
            product = request.form['product']
            cursor.execute('''SELECT id, field3, comm, date, final_cost, final_costpo, SAP_code 
                FROM calculations 
                WHERE field1 = ? AND field2 = ?
                ORDER BY CAST(field3 AS INTEGER)''', 
                (customer, product))

            batches = cursor.fetchall()
            return jsonify({'batches': [[b[0], b[1], b[2], b[3], b[4], b[5], b[6]] for b in batches]})
        elif 'sap_search' in request.form:
            sap_code = request.form['sap_search']
            cursor.execute('''SELECT id, field3, comm, date, final_cost, final_costpo, SAP_code, field2 
                FROM calculations 
                WHERE SAP_code = ?''', 
                (sap_code,))
            batches = cursor.fetchall()
            return jsonify({'batches': [[b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7]] for b in batches]})

    cursor.execute('SELECT DISTINCT field1 FROM calculations ORDER BY field1')
    customers = cursor.fetchall()
    return render_template('select_calculation.html', customers=[c[0] for c in customers])

# --- Скачивание файла базы данных ---
@app.route('/download_db')
@login_required
def download_db():
    """
    Позволяет аутентифицированному пользователю (рекомендуется) скачать файл базы данных SQLite.

    Маршрут: GET /download_db
    Внимание: Доступ к этому маршруту должен быть строго ограничен.

    Возвращает:
        Flask response: Файл базы данных для скачивания или redirect в случае ошибки.
    """
    # db_path = os.path.join('Calculations', 'calculation.db') # Старый вариант
    db_path = config.DB_PATH # Используем config.DB_PATH для консистентности
    if os.path.exists(db_path):
        return send_file(db_path, as_attachment=True)
    else:
        flash("Файл базы данных не найден.")
        return redirect(url_for('start'))


# --- Копирование данных расчета из pickle в сессию (устаревшее) ---
@app.route('/copy', methods=['POST'])
@login_required # Добавлен декоратор
def copy_file():
    with open(request.form["file_path"], 'rb') as file:
        session_data = pickle.load(file)
        session.update(session_data) # Задание в значение session данных из предыдущего расчёта
        session.pop('date', None) 
    return redirect(url_for('home'))

# --- Открытие данных расчета из pickle в сессию (устаревшее) ---
@app.route('/open', methods=['POST'])
def open_file():
    with open(request.form["file_path"], 'rb') as file:
        session_data = pickle.load(file)
        session.update(session_data) # Задание в значение session данных из предыдущего расчёта
    return redirect(url_for('home'))

# --- Удаление файла расчета pickle и связанного excel (устаревшее) ---
@app.route('/delete', methods=['POST'])
@login_required # Добавлен декоратор
def delete_file():
    with open(request.form["file_path"], 'rb') as file:
        session_data = pickle.load(file)
        if "excel_file_name" in session_data:
             os.remove(session_data["excel_file_name"])
    os.remove(request.form["file_path"])    
    return redirect(url_for('start'))

# --- Скачивание excel файла расчета (устаревшее) ---
@app.route('/download', methods=['POST'])
def download_file():
    file_path = request.form["file_path"]
    file_path = ".".join(map(str, file_path.split(".")[:-1])) + ".xlsx"
    with open(file_path, 'rb') as file:
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='text/csv', as_attachment=True) # Скачивание файла
    return redirect(url_for('home'))

# --- Открытие расчета из БД по ID и загрузка в сессию ---
@app.route('/open_file', methods=['POST'])
@login_required
def open_file_db():
    """
    Открывает расчет из базы данных SQLite по ID и загружает его данные в сессию.

    Извлекает все поля для указанного ID, обрабатывает сериализованные
    строки как словари/списки (с использованием eval - ВНИМАНИЕ: РИСК БЕЗОПАСНОСТИ),
    очищает текущую сессию (сохраняя пользователя) и загружает в нее новые данные.

    Маршрут: POST /open_file
    Форм-данные:
        - file_id (int): ID расчета в базе данных.
    """
    file_id_str = request.form.get("file_id")
    if not file_id_str or not file_id_str.isdigit():
        flash("Некорректный ID файла.")
        return redirect(url_for('select_calculation')) # или на страницу выбора
    
    file_id = int(file_id_str)
    db = get_db() # Используем get_db()
    cursor = db.cursor()
    
    # Get all columns except id
    cursor.execute('SELECT * FROM calculations WHERE id = ?', (file_id,))
    columns = [description[0] for description in cursor.description]
    data = cursor.fetchone()
    
    # Create dictionary with all columns
    session_data = {columns[i]: eval(data[i]) if isinstance(data[i], str) and (data[i].startswith('{') or data[i].startswith('[')) else data[i] 
                    for i in range(len(columns))}
    cleaned_data = clean_session_data(session_data)
    session.clear()
    session.update(cleaned_data)

    
    return redirect(url_for('home'))

# --- Копирование расчета из БД по ID и загрузка в сессию (без даты) ---
@app.route('/copy_file', methods=['POST'])
@login_required
def copy_file_db():
    file_id = int(request.form["file_id"])
    db = sqlite3.connect(config.DB_PATH) # Используем config.DB_PATH
    cursor = db.cursor()
    
    # Get all columns except id
    cursor.execute('SELECT * FROM calculations WHERE id = ?', (file_id,))
    columns = [description[0] for description in cursor.description]
    data = cursor.fetchone()
    
    # Create dictionary with all columns, safely handling None values
    session_data = {
        columns[i]: (
            eval(str(data[i]))
            if isinstance(data[i], str) and (data[i].startswith('{') or data[i].startswith('['))
            else data[i]
        )
        for i in range(len(columns)) 
        if columns[i] != 'id' and data[i] is not None  # Skip None values
    }
    
    cleaned_data = clean_session_data(session_data)

    session.clear()
    session.update(cleaned_data)
    session.pop('date', None)
    
    return redirect(url_for('home'))

# --- Скачивание excel файла, связанного с расчетом из БД ---
@app.route('/download_file', methods=['POST'])
@login_required
def download_file_db():
    file_id = int(request.form["file_id"])
    db = sqlite3.connect(config.DB_PATH) # Используем config.DB_PATH
    cursor = db.cursor()
    
    # Get all columns except id
    cursor.execute('SELECT * FROM calculations WHERE id = ?', (file_id,))
    columns = [description[0] for description in cursor.description]
    data = cursor.fetchone()
    
    # Create dictionary with all columns
    session_data = {columns[i]: eval(data[i]) if isinstance(data[i], str) and data[i].startswith('{') else data[i] 
                    for i in range(len(columns)) if columns[i] != 'id'}
    
    file_path = session_data["excel_file_name"]
    with open(file_path, 'rb') as file:
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='text/csv', as_attachment=True) # Скачивание файла

# --- Удаление расчета из БД по ID ---
@app.route('/delete_file', methods=['POST'])
@login_required
def delete_file_db():
    file_id = int(request.form["file_id"])
    db = sqlite3.connect(config.DB_PATH) # Используем config.DB_PATH
    cursor = db.cursor()
        
    cursor.execute('DELETE FROM calculations WHERE id = ?', (file_id,))
    db.commit()
    return redirect(url_for('start'))

# --- Обработка POST-запроса для альтернативной страницы входа неактуально---
@app.route('/login3', methods=['POST'])
def login3():
    username = request.form['username']
    password = request.form['password']

    if ver.authenticate(username, password):
        # Аутентификация прошла успешно
        return 'Успешная аутентификация'
    else:
        # Неправильные учетные данные
        return 'Неправильное имя польазователя или пароль'
    return render_template('login2.html')
    
# --- Основная страница входа (GET/POST) ---
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



# --- Страница создания нового заказчика (сохранение в БД) ---
""" Страница с созданием нового заказчика """
@app.route("/new_customer", methods=['GET', 'POST'])
def cust():
    if request.method == 'POST':
        if 'new' in request.form:
            folder_name = request.form["name"] # Получение имени нового заказчика
            folder_path = Calculations_path + folder_name
            # if not os.path.exists(folder_path): #Если такого имени ещё нет то создаётся новая директория
                # os.makedirs(folder_path)

            db = sqlite3.connect(config.DB_PATH) # Используем config.DB_PATH
            cursor = db.cursor()
            cursor.execute('INSERT INTO customers (customer) VALUES (?)', (folder_name,))
            db.commit()

            return redirect(url_for("home"))
        if 'back' in request.form:
            return redirect(url_for("home"))
    return render_template('Cust.html')

# --- Вспомогательная функция: очистка данных сессии ---
def clean_session_data(session_data):
    cleaned_data = {}
    for key, value in session_data.items():
        if isinstance(value, dict):
            cleaned_sub = {k: v for k, v in value.items() if v and v is not None}
            if cleaned_sub:
                cleaned_data[key] = cleaned_sub
        elif value and (value != "None"):
            cleaned_data[key] = value
    return cleaned_data

# --- Первая страница ввода данных по изделию ---
"""Первая страница с информацией по изделию"""
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    msg = ""
    db = sqlite3.connect(config.DB_PATH) # Используем config.DB_PATH
    cursor = db.cursor()
    cursor.execute('SELECT customer FROM customers')
    file_tree = [row[0] for row in cursor.fetchall()]
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
            msg = ver.home_verif(session) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                if 'id' not in session:
                    session_data = session.copy()
                    if 'home_form' in session_data:
                        home_form_data = dict(session_data['home_form'])
                        session_data = {k: dict(v) if isinstance(v, MultiDict) else v for k, v in session_data.items()}
                        session_data.update(home_form_data)
                    
                    db = sqlite3.connect(config.DB_PATH) # Используем config.DB_PATH
                    cursor = db.cursor()
                    
                    columns = ', '.join(f'"{key}"' for key in session_data.keys())
                    placeholders = ', '.join('?' for _ in session_data.keys())
                    values = [str(value) for value in session_data.values()]
                    
                    cursor.execute(
                        f'INSERT INTO calculations ({columns}) VALUES ({placeholders})',
                        values
                    )
                    session['id'] = cursor.lastrowid
                    db.commit()
                return redirect(url_for('second'))
            else:
                flash(msg) # Вывод всплывающего уведомления о некорректном заполнении
    return render_template('home.html', file_tree=file_tree)

# --- Вторая страница ввода данных (производственная информация) ---
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

# --- Страница просмотра тарифов ---
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

# --- Страница редактирования тарифов ---
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

# --- Страница данных по SMD монтажу ---
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
        if session["tables"] == 0: #Если ошибка 0, т.е в РАР не 2 разных позиций
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

# --- Обработка загрузки файла (BOM/PAP для SMD) ---
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
    
# --- Страница данных по комплектации ---
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
    
# --- Страница данных по THT монтажу ---
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

# --- Страница данных по волновой пайке ---
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

# --- Страница данных по лакировке HRL ---
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

# --- Страница данных по ручному монтажу ---
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

# --- Страница данных по тестированию ---
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

# --- Страница данных по отмывке ---
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

# --- Страница данных по ручной лакировке ---
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

# --- Страница данных по разделению плат ---
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

# --- Страница данных по рентген-контролю ---
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

# --- Страница данных по упаковке ---
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

# --- Страница дополнительных работ ---
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

# --- Страница дополнительных затрат (прибыль, НДС) ---
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

# --- Финальная страница с итоговыми данными и экспортом в Excel ---
@app.route('/session_data', methods=['GET', 'POST'])
@login_required
def session_data():
    df = cm.create_export(session) #Создание таблицы со всеми данными
    session["final_cost"] = str(df[0]["Стоимость 1 ПУ, руб"]["Итоговая стоимость"]) + " руб"
    session["final_costpo"] = str(df[0]["Стоимость на партию, руб"]["Итоговая стоимость"]) + " руб"
    
    # Извлечение данных из df[4] и добавление в сессию
    if len(df) > 4 and not df[4].empty:
        df_comp = df[4]
        try:
            difference_row = df_comp.loc[df_comp['Наименование'] == 'Разница']
            if not difference_row.empty:
                session['difference'] = str(difference_row['Стоимость, руб'].iloc[0])

            difference_percent_row = df_comp.loc[df_comp['Наименование'] == 'Разница в %']
            if not difference_percent_row.empty:
                session['difference_percent'] = str(difference_percent_row['Стоимость, руб'].iloc[0])
        except (IndexError, KeyError):
            # Обработка случая, если строки не найдены
            pass

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
            session["excel_file_name"] = path +"/" + name + ".xlsx"
            session["path_to_dir"] = path
            with pd.ExcelWriter(path +"/" + name + ".xlsx", engine='xlsxwriter') as writer:

                sheet_name = 'Трудозатраты'
                df_info = pd.DataFrame([["Заказчик", session['home_form']['field1']], ["Изделие", session['home_form']['field2']], ["Партия", session['home_form']['field3']], ["Количество м/з", session['second_form']['pc']],
                                        ["Количество компонентов на стороне Top", session["SMD_form"]["components_t"]],
                                        ["Количество компонентов на стороне Bot", session["SMD_form"]["components_b"]],
                                        ["Количество наименований на стороне Top", session["SMD_form"]["unics_t"]],
                                        ["Количество наименований на стороне Bot", session["SMD_form"]["unics_b"]],
                                        ["Количество уникальных наименований", session["SMD_form"]["unics"]]])
                df_info.to_excel(writer, index=False, sheet_name=sheet_name, header = False)
                #df1 = pd.concat([df[0], df[1]], keys=['Стоимость подготовки производства', 'Стоимость производства'])
                start_row = df_info.shape[0] + 2
                df[0].to_excel(writer, sheet_name=sheet_name, startrow= start_row, index=True)
                

                workbook = writer.book
                worksheet = writer.sheets['Трудозатраты']
                wrap_format = workbook.add_format({'text_wrap': False})
                # Создаем формат с обрамлением
                border_format = workbook.add_format({'border': 1, 'text_wrap': False})

                # Применяем формат к каждой ячейке в DataFrame информации о заказе
                for row_num, values in enumerate(df_info.values):
                    for col_num, value in enumerate(values):
                        worksheet.write(row_num, col_num, value, border_format)

                # Создаем формат с автоматическим переносом строки
                wrap_format = workbook.add_format({'text_wrap': False})

                # Применяем формат к каждой ячейке в основной таблице df[0]
                start_row += 1  # Переходим на первую строку с данными основной таблицы
                for row_num, values in enumerate(df[0].values):
                    for col_num, value in enumerate(values):
                        worksheet.write(row_num + start_row, col_num + 1, value, border_format)
                
                    
                # Применяем формат к каждой ячейке в дополнительной таблице df[1]
                if table:
                    start_row += df[0].shape[0] + 2  # Переходим на первую строку с данными дополнительной таблицы
                    for col_num, col_name in enumerate(df[1].columns):
                        worksheet.write(start_row, col_num, col_name, border_format)
                    start_row += 1
                    for row_num, values in enumerate(df[1].values):
                        for col_num, value in enumerate(values):
                            worksheet.write(row_num + start_row, col_num, value, border_format)

                # Настройка ширины столбцов
                worksheet.set_column(0, 0, 45)  # Ширина первого столбца
                for col_num, column in enumerate(df[0].columns):
                    column_length = max(df[0][column].astype(str).map(len).max(), len(column))
                    worksheet.set_column(col_num + 1, col_num + 1, column_length - 3, wrap_format)
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
                
                # Inside the if 'download' in request.form block, add a new sheet after the "Информация" sheet:

                    sheet_name = "Черновая ТК"
                    df[3].to_excel(writer, sheet_name=sheet_name, index=True)

                    workbook = writer.book
                    worksheet = writer.sheets[sheet_name]
                    worksheet.set_landscape()

                    border_format = workbook.add_format({'border': 1})

                    # Write headers with border format
                    for col_num, value in enumerate(df[3].columns):
                        worksheet.write(0, col_num + 1, value, border_format)

                    # Write data and index with border format
                    for row_num, (idx, values) in enumerate(df[3].iterrows()):
                        worksheet.write(row_num + 1, 0, idx, border_format)  # Write index
                        for col_num, value in enumerate(values):
                            worksheet.write(row_num + 1, col_num + 1, value, border_format)

                    # Set column widths
                    worksheet.set_column(0, 0, 10)  # Index column width
                    for col_num, column in enumerate(df[3].columns):
                        column_length = max(df[3][column].astype(str).map(len).max(), len(column))
                        worksheet.set_column(col_num + 1, col_num + 1, column_length + 1)
            session_data = {}
            for key, value in session.items():
                session_data[key] = value

            home_form_data = dict(session_data['home_form'])
            session_data = {k: dict(v) if isinstance(v, MultiDict) else v for k, v in session_data.items()}  # Преобразуем все MultiDict в словари
            session_data.update(home_form_data)
            
            db = sqlite3.connect(config.DB_PATH) # Используем config.DB_PATH
            cursor = db.cursor()
            
            columns = ', '.join(f'"{key}" = ?' for key in session_data.keys())
            values = [str(value) for value in session_data.values()]
                    
            cursor.execute(
                f'''UPDATE calculations 
                    SET {columns}
                    WHERE id = ?''',
                values + [session["id"]]
            )
            db.commit()

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
    if 'home' in request.form:
        clear_session()
        return redirect(url_for('start'))
    if 'catalog' in request.form:
        # dirs = session["path_to_dir"]
        return redirect(url_for('select_calculation'))
    if table:
        return render_template('session_data.html', tables1=[df[0].to_html(classes='table', index=True, header="true")], table=table,
                           tables2=[df[1].to_html(classes='table', index=False, header="true")], 
                           tables3=[df[2].to_html(classes='table', index=False, header="true")],
                           tables4=[df[4].to_html(classes='table', index=False, header="true")])
    return render_template('session_data.html', tables1=[df[0].to_html(classes='table', index=True, header="true")], table = table,
                           tables3=[df[2].to_html(classes='table', index=False, header="true")],
                           tables4=[df[4].to_html(classes='table', index=False, header="true")])

# --- Закрытие соединения с БД после каждого запроса ---
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/block/')
def block_index():
    return send_from_directory('block', 'index.html')

@app.route('/block/<path:filename>')
def block_files(filename):
    return send_from_directory('block', filename)

@app.route('/dashboard_production/')
def dashboard_production_index():
    return send_from_directory('prod', 'index.html')

@app.route('/dashboard_production/<path:filename>')
def dashboard_production_files(filename):
    return send_from_directory('prod', filename)

app.register_blueprint(checklist_bp, url_prefix='/checklist')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    #serve(app, host="0.0.0.0", port=5000)