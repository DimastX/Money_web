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
    if request.method == 'POST':
        session['second_form'] = request.form
        if 'tariffs' in request.form:
            session['last_page'] = 'second'
            return redirect(url_for('tariffs'))
        elif 'back' in request.form:
            return redirect(url_for('home'))
        elif 'next' in request.form:
            return redirect(url_for('third'))
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
"""    df = readdata()
    if request.method == 'POST':
        if 'save' in request.form:
            #df = pd.read_csv('data/tarifs.csv')
            if request.form['row_index'] != "":
                row = int(request.form['row_index'])
                data = request.form['cell_text']
                #df.drop([row], axis=0, inplace=True)
                df["Стоимость, руб/ч"][row] = data  # редактируем второй столбец
                print(df)
            df.to_csv('data/tarifs.csv', index=False)  # сохраняем обратно в csv
            return render_template('tariffs.html', tables=[df.to_html(classes='table', index=False, header="true")])  # возвращаемся к просмотру
    return render_template('edittable.html', tables=[df.to_html(classes='table', index=False, header="true")])"""

@app.route('/update_table', methods=['POST'])
def update_table():
    for key, value in request.form.items():
        row, col = map(int, key.split('-'))
        df.iloc[row, col] = value
    return redirect('/tarrifs')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
