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

from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
password = '1234' # Пароль для редактирования констант
Calculations_path = "Calculations/" # Путь хранения расчётов 

# Загрузка тарифов из таблицы .csv
def readdata():
    return pd.read_csv('data/tarifs.csv')

# Стартовая страница
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


# Страница с каталогом изделий
@app.route('/dirs', methods=['GET', 'POST'])
def dirs():
    file_tree = directories.generate_file_tree('Calculations')  # Путь к директории с заказчиками
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
            # Путь к файлу вида: Директория_хранения/Имя_заказчика/Наименование_изделия/Название_расчёта.pickle
            file_path = Calculations_path + request.form['parent_folder'] + "/" + request.form['child_folder'] + "/" + request.form['sub_folder']
            return send_file(file_path + ".csv", mimetype='text/csv', as_attachment=True) # Скачивание файла 
        if 'new' in request.form:
            return redirect(url_for('cust')) # Открытие страницы с созданием нового заказчика
    return render_template('Dirs.html', file_tree=file_tree)

# Создание списка всех заказчиков
@app.route("/get_child_folders", methods=["POST"])
def get_child_folders():
    parent_folder = request.form["parent_folder"]
    session["dirs1"] = parent_folder # Запись значения имени заказчика в session
    path = Calculations_path+str(parent_folder)
    child_folders = directories.generate_file_tree(path)
    return jsonify({"child_folders": child_folders})


# Создание списка всех изделий
@app.route("/get_sub_folders", methods=["POST"])
def get_sub_folders():
    path = Calculations_path + session['dirs1'] + "/" + str(request.form["child_folder"])
    session["dirs2"] = str(request.form["child_folder"])# Запись значения названия изделия в session
    sub_folders = directories.generate_file_tree2(path)
    return jsonify({"sub_folders": sub_folders})


# Страница с созданием нового заказчика
@app.route("/new_customer", methods=['GET', 'POST'])
def cust():
    if request.method == 'POST':
        if 'new' in request.form:
            folder_name = request.form["name"] # Получение имени нового заказчика
            folder_path = Calculations_path + folder_name
            if not os.path.exists(folder_path): #Если такого имени ещё нет то создаётся новая директория
                os.makedirs(folder_path)
            return redirect(url_for("dirs"))
    return render_template('Cust.html')


# Первая страница в калькуляторе
@app.route('/home', methods=['GET', 'POST'])
def home():
    msg = ""
    file_tree = directories.generate_file_tree('Calculations') # Создание списка всех заказчиков
    if request.method == 'POST':
        session['home_form'] = request.form # Сохранение всех полей 
        if 'back' in request.form:
            return redirect(url_for('start')) # Возвращение на предыдущую страницу
        if 'tariffs' in request.form:
            session['last_page'] = 'home' # Запоминание страницы с которой уходим, для дальнейшего возвращения на неё
            return redirect(url_for('tariffs')) # Открытие страницы с тарифами
        elif 'next' in request.form:
            if (request.form['field1'] != "") and (request.form['field2'] != "") and (request.form['field3'] != ""):
                return redirect(url_for('second'))
            else:
                msg = 'Заполните все поля'
                flash(msg)
        elif 'clear-session-button' in request.form:
            session.clear()
            return redirect(request.url)
    return render_template('home.html', file_tree=file_tree)


@app.route('/second', methods=['GET', 'POST'])
def second():
    msg = ""
    if request.method == 'POST':
        session['second_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'second'
            return redirect(url_for('tariffs'))
        elif 'back' in request.form:
            return redirect(url_for('home'))
        elif 'next' in request.form:
            if ('Comp' in request.form) and ('prod' in request.form) and ('prev' in request.form) \
                    and (request.form['width']!="") and (request.form['length']!="") \
                    and (request.form['width_num']!="") and (request.form['length_num']!="") \
                    and ('Traf' in request.form):
                if request.form['Traf'] =="1":
                    return redirect(url_for('smd'))
                if ('sides_SMD' in request.form) and ('Traf_value' in request.form):
                    if (request.form['Traf'] == "2") and (request.form['sides_SMD']!="") and \
                             (request.form['Traf_value']!=""):
                        return redirect(url_for('smd'))
                if ('sides_SMD' in request.form) and ('Traf_value2' in request.form):
                    if (request.form['Traf'] == "2") and (request.form['sides_SMD']!="") and \
                             (request.form['Traf_value2']!=""):
                        return redirect(url_for('smd'))
                    else:
                        msg = 'Заполните все поля'
                        flash(msg)
                else:
                    msg = 'Заполните все поля'
                    flash(msg)
            else:
                msg = 'Заполните все поля'
                flash(msg)
    return render_template('second.html')


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


@app.route('/SMD', methods=['GET', 'POST'])
def smd():
    edit = "0"
    edit2 = "0"
    df = pd.read_csv('data/SMD.csv')
    df2 = readdata()
    df3 = pd.read_csv('data/SMD2.csv').values.tolist()
    df4 = pd.read_csv('data/SMD2.csv')
    if request.method == 'POST': 
        session['SMD_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'smd'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('second'))
        if 'next' in request.form:
            return redirect(url_for('tht'))
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save2' in request.form:
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/SMD.csv', index=False)
        if 'save3' in request.form:
            if request.form['password2'] == password:
                edit2 = "1"
            else:
                msg = 'Неверный пароль'
                flash(msg)
        if 'save4' in request.form:
            for key in request.form.keys():
                if key.startswith('row_'):  # если используется имя вида 'row%d'
                    row = str(key[4:])  # извлекаем номер строки из имени
                    row = str(row).split("_")
                    df4.iloc[ int(row[0]), int(row[1])-1] = request.form[key]  # обновляем значение ячейки
            df4.to_csv('data/SMD2.csv', index=False)
        if 'template' in request.form:
            return send_file('Documentation/Template.csv', mimetype='text/csv', as_attachment=True)
    return render_template('SMD.html', df=df, df2=df2, edit=edit, df3=df3, edit2=edit2, df4=df4)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    csv_file = request.files['csv_file']
    if csv_file:
        session['tables']=tb.tables(csv_file) 
        return redirect(url_for('smd'))
    else:
        return 'Файл не был загружен'
    

@app.route('/THT', methods=['GET', 'POST'])
def tht():
    edit = "0"
    df = pd.read_csv('data/THT.csv')
    df2 = readdata()
    if request.method == 'POST':
        session['THT_form'] = request.form
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
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/THT.csv', index=False)
    return render_template('THT.html', df=df, df2=df2, edit=edit)

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
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/Wave.csv', index=False)
    return render_template('Wave.html', df=df, df2=df2, edit=edit)

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
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/HRL.csv', index=False)
    return render_template('HRL.html', df=df, df2=df2, edit=edit)

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
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/Hand.csv', index=False)
        if 'next' in request.form:
            if not ('Hand' in request.form):
                return redirect(url_for('test'))
            elif request.form['Hand_num'] != '':
                return redirect(url_for('test'))
            else:
                msg = 'Заполните количество точек пайки'
                flash(msg)
    return render_template('Hand.html', df=df, df2=df2, edit=edit)


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
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/Test.csv', index=False)
        if 'tariffs' in request.form:
            session['last_page'] = 'test'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('hand'))
        if 'next' in request.form:
            if not ('Hand' in request.form):
                return redirect(url_for('clear'))
            elif request.form.__len__() == 3:
                return redirect(url_for('clear'))
            else:
                msg = 'Заполните все поля'
                flash(msg)
    return render_template('Test.html', df=df, df2=df2, edit=edit, rows=rows)


@app.route('/clear', methods=['GET', 'POST'])
def clear():
    edit = "0"
    df = pd.read_csv('data/Clear.csv')
    df2 = readdata()
    data = cm.clear_calculations(session, df)
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
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/Clear.csv', index=False)
        if 'next' in request.form:
            if not ('Clear' in request.form):
                return redirect(url_for('handv'))
            elif 'Clear_type' in request.form:
                return redirect(url_for('handv'))
            else:
                msg = 'Выберите программу отмывки'
                flash(msg)
    return render_template('Clear.html', df = df, edit=edit, data=data, df2=df2)

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
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/Handv.csv', index=False)
    return render_template('Handv.html', df=df, df2=df2, edit=edit)

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
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/Sep.csv', index=False)
        if 'next' in request.form:
            if not ('Sep' in request.form):
                return redirect(url_for('xray'))
            elif 'Sep_type' in request.form:
                if request.form['Sep_type'] == 1:
                    if 'jumpers' in request.form:
                        return redirect(url_for('xray'))
                    else:
                        flash('Заполните количество перемычек')
                else:    
                    return redirect(url_for('xray'))
            else:
                msg = 'Выберите тип разделения'
                flash(msg)
    return render_template('Sep.html', df=df, edit=edit, time=time, df2=df2)


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
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/Xray.csv', index=False)
        if 'next' in request.form:
            if not ('Xray' in request.form):
                return redirect(url_for('add'))
            else:
                if request.form['Xray_proc'] != "":
                    if not ('Xray_type' in request.form):
                        flash('Выберите тип ПУ')
                    elif (request.form['Xray_type'] == "0") or (request.form['Xray_type'] == "1"):
                        return redirect(url_for('add'))
                    elif (request.form['components'] != "") and (request.form['components_time'] != ""):
                        return redirect(url_for('add'))
                    else:
                        return redirect(url_for('add'))
                else:
                    flash('Введите сколько процентов от партии необходимо отправить на контроль')
    return render_template('Xray.html', df=df, df2=df2, edit=edit)


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
            return redirect(url_for('xray'))
        if 'next' in request.form:
            return redirect(url_for('info'))
    return render_template('Add.html', df2=df2)

@app.route('/session_data', methods=['GET', 'POST'])
def session_data():
    df = cm.create_export(session)
    if isinstance(df[1], int):
        table = 0
    else:
        table = 1
    if request.method == 'POST':
        if 'download' in request.form:
            current_time = datetime.now()
            path = "Calculations/" + str(session["home_form"]["field1"]) + "/" + str(session["home_form"]["field2"])
            name = str(session["home_form"]["field1"]) + "_" + str(session["home_form"]["field2"]) + "_" + str(session["home_form"]["field3"]) + "_" + str(current_time.year) + "-" + str(current_time.month) + "-" + str(current_time.day)
            if not os.path.exists(path):
                # Создаем директорию, если она не существует
                os.makedirs(path)
            with open(path +"/" + name + ".csv", 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Заказчик:", session['home_form']['field1']])
                writer.writerow(["Изделие:", session['home_form']['field2']])
                writer.writerow(["Партия:", session['home_form']['field3']])
                writer.writerow([])
                if table:
                    # Записываем пустую строку
                    writer.writerow(["Стоимость подготовки производства"])
                    # Записываем строки из второго DataFrame
                    writer.writerow(df[1].columns)
                    writer.writerows(df[1].to_records(index=False))
                    writer.writerow([])
                writer.writerow(["Стоимость производства"])
                # Записываем строки из первого DataFrame
                writer.writerow(df[0].columns)
                writer.writerows(df[0].to_records(index=True))
            session_data = {}
            for key, value in session.items():
                session_data[key] = value
            with open(path +"/" + name + '.pickle', 'wb') as file:
                pickle.dump(session_data, file)
            return send_file(path +"/" + name + ".csv", mimetype='text/csv', as_attachment=True)
    if 'back' in request.form:
        return redirect(url_for('info'))
    if 'tariffs' in request.form:
        session['last_page'] = 'session_data'
        return redirect(url_for('tariffs'))
    if table:
        return render_template('session_data.html', tables1=[df[0].to_html(classes='table', index=True, header="true")], table=table,
                           tables2=[df[1].to_html(classes='table', index=False, header="true")])
    return render_template('session_data.html', tables1=[df[0].to_html(classes='table', index=True, header="true")], table = table)

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
            for key in request.form.keys():
                if key.startswith('row'):  # если используется имя вида 'row%d'
                    row = int(key[3:])  # извлекаем номер строки из имени
                    df["Значение"][row] = request.form[key]  # обновляем значение ячейки
            df.to_csv('data/Info.csv', index=False)
        if 'next' in request.form:
            return redirect(url_for('session_data'))
        if 'back' in request.form:
            return redirect(url_for('add'))
        if 'tariffs' in request.form:
            session['last_page'] = 'info'
            return redirect(url_for('tariffs'))
    return render_template('Info.html', df=df, edit=edit, df2=df2)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
