from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from flask_table import Table, Col
import pandas as pd
import calculations_money as cm
import io
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'
password = '1234'

def readdata():
    return pd.read_csv('data/tarifs.csv')

@app.route('/', methods=['GET', 'POST'])
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
    fields = 0
    if request.method == 'POST':
        session['SMD_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'smd'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('second'))
        if 'next' in request.form:
            for key in request.form:
                if request.form[key] == '':
                    fields += 1
            if not ('SMD' in request.form):
                return redirect(url_for('tht'))
            elif fields == 1:
                return redirect(url_for('tht'))
            else:
                msg = 'Заполните все поля'
                flash(msg)
    return render_template('SMD.html')

@app.route('/THT', methods=['GET', 'POST'])
def tht():
    fields = 0
    if request.method == 'POST':
        session['THT_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'tht'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('smd'))
        if 'next' in request.form:
            if not ('THT' in request.form):
                return redirect(url_for('wave'))
            elif request.form.__len__() == 3:
                return redirect(url_for('wave'))
            else:
                msg = 'Заполните все поля'
                flash(msg)
    return render_template('THT.html')

@app.route('/wave', methods=['GET', 'POST'])
def wave():
    if request.method == 'POST':
        session['Wave_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'wave'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('tht'))
        if 'next' in request.form:
            if not ('Wave' in request.form):
                return redirect(url_for('HRL'))
            elif request.form.__len__() == 3:
                return redirect(url_for('HRL'))
            else:
                msg = 'Заполните все поля'
                flash(msg)
    return render_template('Wave.html')

@app.route('/HRL', methods=['GET', 'POST'])
def HRL():
    if request.method == 'POST':
        session['HRL_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'HRL'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('wave'))
        if 'next' in request.form:
            if not ('HRL' in request.form):
                return redirect(url_for('hand'))
            elif request.form.__len__() == 3:
                return redirect(url_for('hand'))
            else:
                msg = 'Заполните все поля'
                flash(msg)
    return render_template('HRL.html')

@app.route('/hand', methods=['GET', 'POST'])
def hand():
    if request.method == 'POST':
        session['Hand_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'hand'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('HRL'))
        if 'next' in request.form:
            if not ('Hand' in request.form):
                return redirect(url_for('test'))
            elif request.form.__len__() == 3:
                return redirect(url_for('test'))
            else:
                msg = 'Заполните все поля'
                flash(msg)
    return render_template('Hand.html')


@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        session['Test_form'] = request.form
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
    return render_template('Test.html')


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
    if request.method == 'POST':
        session['Handv_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'handv'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('clear'))
        if 'next' in request.form:
            if not ('Handv' in request.form):
                return redirect(url_for('sep'))
            elif request.form.__len__() == 3:
                return redirect(url_for('sep'))
            else:
                msg = 'Заполните все поля'
                flash(msg)
    return render_template('Handv.html')

@app.route('/separation', methods=['GET', 'POST'])
def sep():
    df = pd.read_csv('data/Sep.csv')
    fields = 0
    edit = "0"
    time = cm.sep_calculations(session, df)
    if request.method == 'POST':
        session['Sep_form'] = request.form
        if 'save' in request.form:
            if request.form['password'] == password:
                edit = "1"
            else:
                msg = 'Правильно заполните поля'
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
    return render_template('Sep.html', df=df, edit=edit, time=time)


@app.route('/xray', methods=['GET', 'POST'])
def xray():
    fields = 0
    if request.method == 'POST':
        session['Xray_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'xray'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('sep'))
        if 'next' in request.form:
            for key in request.form:
                if request.form[key] == '':
                    fields += 1
            if not ('Xray' in request.form):
                return redirect(url_for('add'))
            elif fields == 1:
                return redirect(url_for('add'))
            else:
                msg = 'Заполните все поля'
                flash(msg)
    return render_template('Xray.html')


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

@app.route('/session_data')
def session_data():
    # Отображаем данные из объекта session на странице
    session_data = []
    i = 0
    for key, value in session.items():
        session_data.append({'key': key, 'value': value})
        session_data[i]['value'] = str(session_data[i]['value']).translate(str.maketrans('{}', "  "))
        session_data[i]['value'] = str(session_data[i]['value']).replace(',', "<br>")
        print(session_data[i]['value'])
        i=i+1

    return render_template('session_data.html', session_data=session_data)

@app.route('/download')
def download():
    # Создаем CSV-файл на сервере
    csv_data = create_csv()

    # Отправляем файл в качестве вложения для скачивания
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=session_data.csv'
    return response

def create_csv():
    # Создаем объект io.StringIO для записи CSV-файла в память
    csv_buffer = io.StringIO()

    # Записываем таблицу в CSV-файл
    writer = csv.writer(csv_buffer)
    writer.writerow(['Field', 'Value'])
    for key, value in session.items():
        writer.writerow([key, value])

    return csv_buffer.getvalue()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
