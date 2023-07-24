from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
app = Flask(__name__)
app.secret_key = 'your_secret_key'


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
                #return render_template('home.html', msg=msg)
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
            if (request.form['Comp']!="") and (request.form['prod']!="") and (request.form['prev']!="") \
                    and (request.form['width']!="") and (request.form['length']!="") \
                    and (request.form['width_num']!="") and (request.form['length_num']!="") \
                    and (request.form['multi']!="") and ('Traf' in request.form):
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
            if request.form['password'] == '1234':
                #return render_template('edittable.html', tables=[df.to_html(classes='table', index=False, header="true")])
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

@app.route('/update_table', methods=['POST'])
def update_table():
    for key, value in request.form.items():
        row, col = map(int, key.split('-'))
        df.iloc[row, col] = value
    return redirect('/tarrifs')


@app.route('/SMD', methods=['GET', 'POST'])
def smd():
    if request.method == 'POST':
        session['SMD_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'smd'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('second'))
        if 'next' in request.form:
            if not ('SMD' in request.form):
                return redirect(url_for('tht'))
            else:
                msg = 'Заполните все поля'
                flash(msg)
    return render_template('SMD.html')

@app.route('/THT', methods=['GET', 'POST'])
def tht():
    if request.method == 'POST':
        session['tht_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'tht'
            return redirect(url_for('tariffs'))
        if 'back' in request.form:
            return redirect(url_for('smd'))
        if 'next' in request.form:
            if request.rorm['tht'] == False:
                return redirect(url_for('THT'))
    return render_template('THT.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
