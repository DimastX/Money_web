from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, Response, jsonify
from flask_table import Table, Col
import pandas as pd
import calculations_money as cm
import io
import csv
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename
import tables as tb
import directories
import pickle
import Verification as ver
import time

from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
password = '1234' # Пароль для редактирования констант
Calculations_path = "Calculations/" # Путь хранения расчётов 

""" Функция для загрузки тарифов из таблицы .csv"""
def readdata():
    return pd.read_csv('data/tarifs.csv')

"""Стартовая страница"""
@app.route('/', methods=['GET', 'POST'])
def start():
    if request.method == 'POST':
        # Очистка cookies и открытие формы расчёта
        if 'next' in request.form:
            session.clear()
            return redirect(url_for('home'))
        # Открытие каталога изделий
        if 'dirs' in request.form:
            return redirect(url_for('dirs'))
    return render_template('Start.html') #Открытие стартовой станицы


"""Страница с каталогом изделий"""
@app.route('/dirs', methods=['GET', 'POST'])
def dirs():
    file_tree = directories.generate_file_tree('Calculations')  # Путь к директории с заказчиками
    session.clear()
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
                    send_file(file_path + ".xlsx", mimetype='text/csv', as_attachment=True) # Скачивание файла 
                if os.path.exists(file_path + ".csv"):
                    send_file(file_path + ".csv", mimetype='text/csv', as_attachment=True) # Скачивание файла ``
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
def home():
    msg = ""
    file_tree = directories.generate_file_tree('Calculations') # Создание списка всех заказчиков
    if request.method == 'POST':
        session['home_form'] = request.form # Сохранение всех полей в случае отправки формы
        ver.auto_save(session)
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
        ver.auto_save(session)
        if 'tariffs' in request.form:
            session['last_page'] = 'smd'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('second'))
        if 'next' in request.form:
            msg = ver.smd_verif(session) # Вызов проверки заполнения полей на первой странице
            if msg == 0:
                return redirect(url_for('tht')) #Переход на следующую страницу
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
    
"""THT монтаж"""
@app.route('/THT', methods=['GET', 'POST'])
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
            return redirect(url_for('smd'))
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
def wave():
    edit = "0"
    df = pd.read_csv('data/Wave.csv')
    df2 = readdata()
    if request.method == 'POST':
        session['Wave_form'] = request.form
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
def HRL():
    edit = "0"
    df = pd.read_csv('data/HRL.csv')
    df2 = readdata()
    if request.method == 'POST':
        session['HRL_form'] = request.form
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
def hand():    
    edit = "0"
    df = pd.read_csv('data/Hand.csv')
    df2 = readdata()
    if request.method == 'POST':
        session['Hand_form'] = request.form
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
def test():
    edit = "0"
    df2 = readdata()
    df = pd.read_csv('data/Test.csv')
    rows = 0
    if request.method == 'POST': 
        session['Test_form'] = request.form
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
def clear():
    edit = "0"
    df = pd.read_csv('data/Clear.csv')
    df2 = readdata()
    data = cm.clear_calculations(session, df) #
    if request.method == 'POST':
        session['Clear_form'] = request.form
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
def handv():
    edit = "0"
    df = pd.read_csv('data/Handv.csv')
    df2 = readdata()
    if request.method == 'POST':
        session['Handv_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'handv'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('clear'))
        if 'next' in request.form:
            return redirect(url_for('sep'))
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
def sep():
    df = pd.read_csv('data/Sep.csv')
    df2 = readdata()
    fields = 0
    edit = "0"
    time = cm.sep_calculations(session, df)
    if request.method == 'POST':
        session['Sep_form'] = request.form
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
def xray():
    fields = 0
    edit = "0"
    df2 = readdata()
    df = pd.read_csv('data/Xray.csv')
    if request.method == 'POST':
        session['Xray_form'] = request.form
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
def pack():
    df = pd.read_csv('data/Pack.csv')
    df2 = readdata()
    fields = 0
    edit = "0"
    if request.method == 'POST':
        session['Pack_form'] = request.form
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
def add():
    fields = 0
    df2 = readdata()
    if request.method == 'POST':
        session['Add_form'] = request.form
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
def info():
    edit = "0"
    df2 = readdata()
    df = pd.read_csv('data/Info.csv')
    if request.method == 'POST':
        session['Info_form'] = request.form
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
def session_data():
    df = cm.create_export(session) #Создание таблицы со всеми данными
    if isinstance(df[1], int):
        table = 0
    else:
        table = 1
    session['check'] = 1
    if request.method == 'POST':
        session["session_data"] = request.form
        if 'download' in request.form:
            current_time = datetime.now()
            path = "Calculations/" + str(session["home_form"]["field1"]) + "/" + str(session["home_form"]["field2"])
            name = str(session["home_form"]["field1"]) + "_" + str(session["home_form"]["field2"]) + "_" + str(session["home_form"]["field3"]) + "_" + str(current_time.year) + "-" + str(current_time.month) + "-" + str(current_time.day)
            if "comm" in session["home_form"]:
                if session["home_form"] != "":
                    name += "_" + session["home_form"]["comm"]
            if not os.path.exists(path):
                os.makedirs(path)

            with pd.ExcelWriter(path +"/" + name + ".xlsx") as writer:

                sheet_name = 'Трудозатраты'
                df_info = pd.DataFrame([["Заказчик", session['home_form']['field1']], ["Изделие", session['home_form']['field2']], ["Партия", session['home_form']['field3']]])
                df_info.to_excel(writer, index=False, sheet_name=sheet_name, header = False)
                #df1 = pd.concat([df[0], df[1]], keys=['Стоимость подготовки производства', 'Стоимость производства'])
                start_row = df_info.shape[0] + 2
                df[0].to_excel(writer, sheet_name=sheet_name, startrow= start_row, index=True)
                if table:
                    start_row += df[0].shape[0] + 2
                    df[1].to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False)
                for column in df[0]:
                    column_length = max(df[0][column].astype(str).map(len).max(), len(column))
                    col_idx = df[0].columns.get_loc(column)
                    writer.sheets[sheet_name].set_column(col_idx + 1, col_idx + 1, column_length+1)
                writer.sheets[sheet_name].set_column(0, 0, 60)
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
    if table:
        return render_template('session_data.html', tables1=[df[0].to_html(classes='table', index=True, header="true")], table=table,
                           tables2=[df[1].to_html(classes='table', index=False, header="true")])
    return render_template('session_data.html', tables1=[df[0].to_html(classes='table', index=True, header="true")], table = table)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
    #serve(app, host="0.0.0.0", port=5000)
