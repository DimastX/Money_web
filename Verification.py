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
        if form["money_all_f"] == 'NaN руб':
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