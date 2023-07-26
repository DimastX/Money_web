import math

def clear_calculations(session, df):
    by_x = math.floor(df['Значение'][3] / float(session['second_form']['width']))
    by_y = math.floor(df['Значение'][2] / float(session['second_form']['length']))
    number_multi = by_x * by_y
    number_items = int(session['second_form']['length_num']) * int(session['second_form']['width_num'])
    return [number_multi, number_items]