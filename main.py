from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, Response
from flask_table import Table, Col
import pandas as pd
import calculations_money as cm
import io
import csv
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename
import tables as tb

app = Flask(__name__)
app.secret_key = 'your_secret_key'
password = '1234'

def readdata():
    return pd.read_csv('data/tarifs.csv')

@app.route('/', methods=['GET', 'POST'])
def start():
    if request.method == 'POST':
        if 'next' in request.form:
            return redirect(url_for('home'))
    return render_template('Start.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    msg = ""
    if request.method == 'POST':
        session['home_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'home'
            return redirect(url_for('tariffs'))
        elif 'next' in request.form:
            if (request.form['field1'] != "") and (request.form['field2'] != "") and (request.form['field3'] != ""):
                return redirect(url_for('second'))
            else:
                msg = 'Заполните все поля'
                #return render_template('home.html', msg=msg)ss
                flash(msg)
        elif 'clear-session-button' in request.form:
            session.clear()
            return redirect(request.url)
    return render_template('home.html')


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
                    and ('multi' in request.form) and ('Traf' in request.form):
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
    df = pd.read_csv('data/SMD.csv')
    df2 = readdata()
    df3 = pd.read_csv('data/SMD2.csv').values.tolist()
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
    return render_template('SMD.html', df=df, df2=df2, edit=edit, df3=df3)


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
    """if 'field1_values' in session['Test_form']:
        rows = max(len(session['Test_form']['field1_values']), rows)
    if 'field2_values' in session['Test_form']:
        rows = max(len(session['Test_form']['field2_values']), rows)"""
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
            return redirect(url_for('session_data'))
    return render_template('Add.html', df2=df2)

@app.route('/session_data', methods=['GET', 'POST'])
def session_data():
    df = cm.create_export(session)
    if request.method == 'POST':
        if 'download' in request.form:
            df[1].to_csv('Calculations/Prepare.csv', sep=',', encoding='utf-8')
            df[0].to_csv('Calculations/Data.csv', sep=',', encoding='utf-8')
        
            # Возвращаем файл для скачивания.
            return send_file('Calculations/data.csv', mimetype='text/csv', as_attachment=True)
    if 'back' in request.form:
        return redirect(url_for('add'))
    if 'tariffs' in request.form:
        session['last_page'] = 'session_data'
        return redirect(url_for('tariffs'))
    return render_template('session_data.html', tables1=[df[0].to_html(classes='table', index=True, header="true")], 
                           tables2=[df[1].to_html(classes='table', index=False, header="true")])


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
