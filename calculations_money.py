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

def sep_calculations(session, df):
    by_x = float(session['second_form']['width']) * (int(session['second_form']['length_num']) + 1) 
    by_y = float(session['second_form']['length']) * (int(session['second_form']['width_num']) + 1) 
    number_items = int(session['second_form']['length_num']) * int(session['second_form']['width_num'])
    number_multi = int(session['home_form']['field3']) /  number_items
    time_scrub = math.ceil((by_x + by_y) / df['Значение'][0] * df['Значение'][3] / number_items)
    time_jump = df['Значение'][1] * df['Значение'][4]
    time_sar = math.ceil((by_x + by_y) / df['Значение'][2] * df['Значение'][5] / number_items)
    time = [time_scrub, time_jump, time_sar, number_multi, number_items]
    return time