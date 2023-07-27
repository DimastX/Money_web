import math

def clear_calculations(session, df):
    by_x = math.floor(df['Значение'][3] / float(session['second_form']['width']))
    by_y = math.floor(df['Значение'][2] / float(session['second_form']['length']))
    number_multi = int(by_x * by_y)
    number_items = int(session['second_form']['length_num']) * int(session['second_form']['width_num'])
    number_smallitems = int(number_items * number_multi)
    if int(session['home_form']['field3']) < number_smallitems:
        number_smallitems = int(session['home_form']['field3'])
        number_multi = number_smallitems / number_items
    return [number_multi, number_items, number_smallitems]