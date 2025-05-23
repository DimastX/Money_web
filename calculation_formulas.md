# Формулы расчета стоимости производства

Этот документ описывает основные формулы, используемые для расчета времени и стоимости различных операций в веб-приложении, исходя из анализа кода (`main.py`, `.html` шаблоны с JavaScript) и файлов данных (`.csv`).

**Обозначения:**

*   `t_` префикс для времени (time).
*   `cost_` префикс для стоимости (money).
*   `_all` суффикс для общего значения по партии.
*   `_pc` суффикс для значения на 1 производственную единицу (ПУ).
*   Переменные из сессии обозначаются `{session['key']}`.
*   Константы из `.csv` файлов обозначаются `{df['Название колонки'][индекс строки]}` или `{df2['Название колонки'][индекс строки]}`. Индексы строк соответствуют порядку в файле `.csv`.
*   Переменные из полей ввода на странице обозначаются по их `id` или `name` в HTML.
*   Промежуточные переменные и расчеты описываются отдельно.

# 1. Исходные данные (/second)

На этой странице вводятся общие параметры мультизаготовки (МЗ), отдельной платы (ПП), а также другие параметры, влияющие на последующие расчеты стоимости и времени производства. Данные сохраняются в сессии и используются на следующих этапах калькуляции.

**Входные параметры (со страницы `/home`):**

*   `quantity`: Общее количество ПУ (плат) в партии (из `session['home_form']['field3']`).

**Входные параметры (со страницы `/second`):**

*   **Параметры мультизаготовки (МЗ):**
    *   `width`: Ширина мультизаготовки (МЗ), мм (поле `width`, сохраняется в `session['second_form']['width']`).
    *   `length`: Длина мультизаготовки (МЗ), мм (поле `length`, сохраняется в `session['second_form']['length']`).
    *   `width_num`: Количество плат в ширину на МЗ (поле `width_num`, сохраняется в `session['second_form']['width_num']`).
    *   `length_num`: Количество плат в длину на МЗ (поле `length_num`, сохраняется в `session['second_form']['length_num']`).
    *   `multi_num`: Общее количество МЗ в партии (рассчитывается в JS как `quantity / (width_num * length_num)`, если `width_num * length_num > 0`, иначе 0; сохраняется в `session['second_form']['multi_num']`).
    *   `board_thickness`: Толщина платы, мм (поле `thickness`, сохраняется в `session['second_form']['thickness']`).

*   **Параметры производственной единицы (ПУ) / платы (рассчитываются в JavaScript на странице `/second` и сохраняются в сессии):**
    *   `width_pp`: Ширина одной платы (ПП), мм (поле `width_pp`). Рассчитывается как `width / width_num` (если `width_num > 0`, иначе 0). Сохраняется в `session['second_form']['width_pp']`.
    *   `length_pp`: Длина одной платы (ПП), мм (поле `length_pp`). Рассчитывается как `length / length_num` (если `length_num > 0`, иначе 0). Сохраняется в `session['second_form']['length_pp']`.
    *   `board_square`: Площадь одной платы (ПП), мм² (поле `square`). Рассчитывается как `width_pp * length_pp`. Сохраняется в `session['second_form']['square']`.

*   **Прочие параметры (сохраняются в `session['second_form']`):**
    *   `Comp`: Тип комплектации (радио-кнопки `Comp`, значения `1`-`4`).
    *   `prepare`: Флажок "Выполнять подготовку производства?" (чекбокс `prepare`, значение `1` если отмечен).
    *   `prod`: Место производства (радио-кнопки `prod`, значения `1`-`2`).
    *   `prev`: Производилось ли ранее (радио-кнопки `prev`, значения `1`-`2`).
    *   `Traf`: Тип трафаретов (радио-кнопки `Traf`, значения `1`-`2`):
        *   `1`: Давальческие
        *   `2`: Разрабатывает Starline
            *   `sides_SMD`: Количество сторон SMD (радио-кнопки `sides_SMD`, значения `1`-`2`).
            *   `Trafs_costs_select`: Выбор способа задания стоимости трафарета (радио-кнопки `Trafs_costs_select`, значения `1`-`2`):
                *   `1`: Тарифная
                *   `2`: Ручная
            *   `Traf_value2`: Выбор тарифной стоимости трафарета (выпадающий список `Traf_value2`, значения `1`-`3`, соответствующие разным стоимостям).
            *   `Traf_value`: Ручной ввод стоимости трафарета (поле `Traf_value`).
    *   `cost_c`: Стоимость компонентов на всю партию (поле `cost_c`).
    *   `cost_p`: Стоимость печатных плат на всю партию (поле `cost_p`).
    *   `cost_e`: Стоимость оснасток на всю партию (поле `cost_e`).

**Расчеты на странице не производятся, кроме автоматического вычисления `width_pp`, `length_pp`, `board_square` и `multi_num` в JavaScript при изменении соответствующих полей.** Введенные и рассчитанные данные сохраняются в сессии для использования на последующих страницах.

# 2. SMD монтаж (/smd)

На этой странице рассчитывается время и стоимость автоматического поверхностного монтажа (SMT) компонентов на печатные платы. Расчеты производятся в JavaScript-функции `SMD_amount()` в шаблоне `SMD.html` и учитывают множество параметров, включая количество компонентов, наименований, время на переналадку, ремонт, контроль и АОИ.

**Входные параметры (со страницы `/home` и `/second` через сессию):**

*   `quantity`: Общее количество ПУ (плат) в партии (из `session['home_form']['field3']`).
*   `multi_num`: Общее количество МЗ в партии (из `session['second_form']['multi_num']`).
*   `board_width`: Ширина МЗ, мм (из `session['second_form']['width']`).
*   `board_length`: Длина МЗ, мм (из `session['second_form']['length']`).
*   `prev_production_type`: Тип предыдущей операции (из `session['second_form']['prev']`, значения `1` или `2`), влияет на процент брака для расчета ремонта.

**Входные параметры (со страницы `/smd`):**

*   `SMD_active`: Чекбокс "Выполнять автоматический поверхностный монтаж SMT?" (поле `SMD`). Если не отмечен, расчеты не производятся.
*   `SMD1` (или `lines[0]` в JS): Количество компонентов на стороне Top (поле `SMD1`).
*   `SMD2` (или `lines[1]` в JS): Количество наименований на стороне Top (поле `SMD2`).
*   `SMD3` (или `lines[2]` в JS): Количество компонентов на стороне Bot (поле `SMD3`).
*   `SMD4` (или `lines[3]` в JS): Количество наименований на стороне Bot (поле `SMD4`).
*   `SMD5` (или `lines[4]` в JS): Количество уникальных наименований (общее) (поле `SMD5`).
*   `use_simulation`: Чекбокс "Использовать симуляцию?" (поле `SMD_sim`).
    *   `Sim_top_time`: Время по симуляции на Top сторону для 1 МЗ, с (поле `Sim_top`).
    *   `Sim_bot_time`: Время по симуляции на Bot сторону для 1 МЗ, с (поле `Sim_bot`).

**Константы из файлов данных:**

*   `data/SMD.csv` (загружается в `df` в Python, передается в JS):
    *   `df['Значение'][0]`: Общий поправочный коэффициент времени линии SMT.
    *   `df['Значение'][1]`: Минимальное время переналадки на одну сторону, с.
    *   `df['Значение'][2]`: Время переналадки на одно наименование, с.
    *   `df['Значение'][3]`: Постоянное время переналадки на одну сторону, с.
    *   `df['Значение'][4]`: Процент брака для ремонта (если `prev_production_type == 2`).
    *   `df['Значение'][5]`: Процент брака для ремонта (если `prev_production_type == 1`).
    *   `df['Значение'][6]`: Норматив времени на ремонт 1 шт, с.
    *   `df['Значение'][7]`: Норматив времени на контроль 1 шт, с.
    *   `df['Значение'][8]`: Минимальное производственное время на 1 МЗ, с.
    *   `df['Значение'][9]`: Длина области АОИ, мм (`length_AOI`).
    *   `df['Значение'][10]`: Ширина области АОИ, мм (`width_AOI`).
    *   `df['Значение'][11]`: Дополнительное время на 1 цикл АОИ, с (`AOI_time_add`).
*   `data/SMD2.csv` (загружается в `df3` и `df4` в Python, `df3` передается в JS как массив `df` для функции `speed_amount`):
    *   Содержит диапазоны количества компонентов и соответствующую им скорость монтажа (компоненты/час).
*   `data/variables.csv` (загружается функцией `readdata()` в `df2` в Python, передается в JS):
    *   `df2['Стоимость, руб/ч'][0]`: Стоимость часа работы линии SMT.
    *   `df2['Стоимость, руб/ч'][1]`: Стоимость часа работы наладчика SMT.
    *   `df2['Стоимость, руб/ч'][8]`: Стоимость часа работы ремонтника.
    *   `df2['Стоимость, руб/ч'][21]`: Стоимость часа работы контролера.

**Основные этапы расчета (в функции `SMD_amount()`):**

1.  **Определение количества активных сторон:** `sides` (1 или 2) в зависимости от наличия компонентов на Top (`SMD1 > 0`) и Bot (`SMD3 > 0`).

2.  **Расчет времени и стоимости ремонта:**
    *   `num_repair_items = df['Значение'][индекс_брака] * quantity`
    *   `t_repair_all_hours = ceil(num_repair_items * df['Значение'][6] / 100 / 3600)`
    *   `cost_repair_all = ceil(t_repair_all_hours * df2['Стоимость, руб/ч'][8])`

3.  **Расчет времени и стоимости контроля ремонта:**
    *   `t_control_repair_all_hours = ceil(num_repair_items * df['Значение'][7] / 100 / 3600)`
    *   `cost_control_repair_all = ceil(t_control_repair_all_hours * df2['Стоимость, руб/ч'][21])`

4.  **Определение количества компонентов и наименований:**
    *   `total_components_batch_top = SMD1 * quantity`
    *   `total_components_batch_bot = SMD3 * quantity`
    *   `num_unique_names_top = SMD2`
    *   `num_unique_names_bot = SMD4`

5.  **Определение скорости монтажа (функция `speed_amount(num_components_on_side_batch)`):**
    Скорость выбирается из таблицы `data/SMD2.csv` на основе общего количества компонентов на соответствующей стороне партии (`total_components_batch_top` или `total_components_batch_bot`).
    *   `speed_top = speed_amount(total_components_batch_top)` (компоненты/час)
    *   `speed_bot = speed_amount(total_components_batch_bot)` (компоненты/час)

6.  **Расчет времени АОИ на 1 МЗ (`t_aoi_mz_hours`):**
    *   `t_aoi_mz_hours = (board_width * board_length / (width_AOI * length_AOI) + AOI_time_add) / 3600` (это время на одну МЗ, далее умножается на `multi_num` для получения общего времени АОИ на партию)
    *   `t_aoi_batch_hours = t_aoi_mz_hours * multi_num`

7.  **Расчет времени переналадки для каждой стороны (`t_setup_side_hours`):**
    *   Для Top: `t_setup_top_hours = max(num_unique_names_top * df['Значение'][2] + df['Значение'][3], df['Значение'][1]) / 3600` (если `num_unique_names_top > 0`, иначе 0)
    *   Для Bot: `t_setup_bot_hours = max(num_unique_names_bot * df['Значение'][2] + df['Значение'][3], df['Значение'][1]) / 3600` (если `num_unique_names_bot > 0`, иначе 0)
    *   `t_setup_total_hours = t_setup_top_hours + t_setup_bot_hours`

8.  **Расчет производственного времени для каждой стороны (`t_prod_side_hours`):**
    *   Если не используется симуляция:
        *   `t_prod_top_hours_calc = ceil(total_components_batch_top / speed_top)` (если `speed_top > 0` и `SMD1 > 0`, иначе 0)
        *   `t_prod_bot_hours_calc = ceil(total_components_batch_bot / speed_bot)` (если `speed_bot > 0` и `SMD3 > 0`, иначе 0)
        *   Корректировка с учетом минимального времени на МЗ: 
            `t_prod_top_hours = max(t_prod_top_hours_calc, multi_num * df['Значение'][8] / 3600)` (если `SMD1 > 0`)
            `t_prod_bot_hours = max(t_prod_bot_hours_calc, multi_num * df['Значение'][8] / 3600)` (если `SMD3 > 0`)
    *   Если используется симуляция:
        *   `t_prod_top_hours = Sim_top_time * multi_num / 3600`
        *   `t_prod_bot_hours = Sim_bot_time * multi_num / 3600`
    *   Корректировка с учетом времени АОИ (если АОИ дольше производственного времени на стороне):
        *   `t_prod_top_hours = max(t_prod_top_hours, t_aoi_batch_hours)` (если `SMD1 > 0`)
        *   `t_prod_bot_hours = max(t_prod_bot_hours, t_aoi_batch_hours)` (если `SMD3 > 0`)
    *   `t_prod_total_hours = t_prod_top_hours + t_prod_bot_hours`

9.  **Общее время сборки партии с коэффициентом (`t_assembly_total_batch_hours`):**
    *   `t_assembly_total_batch_hours = ceil(t_prod_total_hours * df['Значение'][0])`
    *   Аналогично для каждой стороны: `t_assembly_top_batch_hours`, `t_assembly_bot_batch_hours`.

10. **Общее время переналадки партии с коэффициентом (`t_setup_total_batch_hours`):**
    *   `t_setup_total_batch_hours = ceil(t_setup_total_hours * df['Значение'][0])`
    *   Аналогично для каждой стороны: `t_setup_top_batch_hours`, `t_setup_bot_batch_hours`.

11. **Стоимость сборки партии (`cost_assembly_total_batch`):**
    *   `cost_assembly_total_batch = ceil(t_assembly_total_batch_hours * df2['Стоимость, руб/ч'][0])`
    *   Аналогично для каждой стороны.

12. **Стоимость переналадки партии (`cost_setup_total_batch`):**
    *   `cost_setup_total_batch = ceil(t_setup_total_batch_hours * df2['Стоимость, руб/ч'][1])`
    *   Аналогично для каждой стороны.

13. **Итоговые время и стоимость на 1 ПУ и на всю партию:**
    Рассчитываются делением соответствующих общих значений на `quantity` (с округлением вверх для стоимости и времени на ПУ в секундах).

    *   **Общее время на всю партию (`t_all_SMD_hours`):** Это непрямая сумма, а скорее отображение `time_all` из JS, которое является `t_assembly_total_batch_hours`.
    *   **Общая стоимость на всю партию (`cost_all_SMD`):**
        $$ \text{cost\_all\_SMD} = \text{cost\_assembly\_total\_batch} + \text{cost\_setup\_total\_batch} + \text{cost\_repair\_all} + \text{cost\_control\_repair\_all} $$ 

    *   **Общее время на 1 ПУ (`t_pc_SMD_seconds`):**
        $$ t_{pc\_SMD\_seconds} = \lceil (\text{t\_assembly\_total\_batch\_hours} + \text{t\_setup\_total\_batch\_hours}) \times 3600 / \text{quantity} \rceil + \lceil (\text{t\_repair\_all\_hours} + \text{t\_control\_repair\_all\_hours}) \times 3600 / \text{quantity} \rceil $$ 
        *(Примечание: в JS расчет времени на ПУ для ремонта и контроля не суммируется с основным временем, а отображается отдельно. Здесь приведена общая концепция.)*

    *   **Общая стоимость на 1 ПУ (`cost_pc_SMD`):**
        $$ \text{cost\_pc\_SMD} = \lceil \text{cost\_all\_SMD} / \text{quantity} \rceil $$ 

На странице также отображается детализация времени и стоимости по сторонам (Top/Bot) для сборки и переналадки.

Если чекбокс `SMD_active` не отмечен, все поля на странице отображают "-".

# 3. Комплектация (/comp)

На странице рассчитывается общее время и стоимость работ по комплектации заказа, включая приемку, входной контроль, выходной контроль и отгрузку. Расчеты производятся в JavaScript-функции `Comp_amount()` в шаблоне `Comp.html`.

**Входные параметры (со страницы `/home` через сессию):**

*   `quantity`: Общее количество ПУ (плат) в партии (из `session['home_form']['field3']`).

**Входные параметры (со страницы `/comp`):**

*   `num_positions`: Количество наименований по накладной (поле `Comp_num`).
*   `product_type`: Тип изделия (выбирается radio-кнопками `Comp_type`):
    *   `1`: Серверная плата
    *   `2`: Материнская плата
    *   `3`: Маленькая плата
    *   `4`: Средняя плата

**Константы из файлов данных:**

*   `data/Comp.csv` (загружается в `df` в Python, значения передаются в JS):
    *   `df['Значение'][0]`: Базовое время на приемку одного наименования, с/наименование.
    *   `df['Значение'][1]`: Базовое время на входной контроль одного наименования, с/наименование.
    *   `df['Значение'][2]`: Время на выходной контроль для типа "Серверная плата", с/ПУ.
    *   `df['Значение'][3]`: Базовое время на отгрузку 1 ПУ, с/ПУ.
    *   `df['Значение'][4]`: Минимальное общее время на входной контроль партии, с.
    *   `df['Значение'][6]`: Время на выходной контроль для типа "Материнская плата", с/ПУ.
    *   `df['Значение'][7]`: Время на выходной контроль для типа "Маленькая плата", с/ПУ.
    *   `df['Значение'][8]`: Время на выходной контроль для типа "Средняя плата", с/ПУ.
    *   `df['Значение'][9]`: Дополнительное (базовое) время на выходной контроль 1 ПУ, с/ПУ (прибавляется к времени по типу изделия).
*   `data/variables.csv` (загружается функцией `readdata()` в `df2` в Python, значения передаются в JS):
    *   `df2['Стоимость, руб/ч'][19]`: Стоимость часа работы для входного контроля.
    *   `df2['Стоимость, руб/ч'][21]`: Стоимость часа работы для выходного контроля.
    *   `df2['Стоимость, руб/ч'][22]`: Стоимость часа работы для приемки и отгрузки.

**Расчеты (в `Comp.html` - функция `Comp_amount()`):**

1.  **Приемка:**
    *   Время на приемку всей партии (`t_acceptance_all_hours`):
        $$ t_{\text{acceptance\_all\_hours}} = \lceil (\text{num\_positions} \times \text{df['Значение'][0]}) / 3600 \rceil $$
    *   Стоимость приемки всей партии (`cost_acceptance_all`):
        $$ \text{cost\_acceptance\_all} = t_{\text{acceptance\_all\_hours}} \times \text{df2['Стоимость, руб/ч'][22]} $$
    *   Время на приемку 1 ПУ (`t_acceptance_pc_seconds`):
        $$ t_{\text{acceptance\_pc\_seconds}} = \lceil (t_{\text{acceptance\_all\_hours}} \times 3600) / \text{quantity} \rceil $$
    *   Стоимость приемки 1 ПУ (`cost_acceptance_pc`):
        $$ \text{cost\_acceptance\_pc} = \lceil \text{cost\_acceptance\_all} / \text{quantity} \rceil $$

2.  **Входной контроль:**
    *   Базовое время на входной контроль всей партии (`t_incoming_control_base_all_hours`):
        $$ t_{\text{incoming\_control\_base\_all\_hours}} = \lceil (\text{num\_positions} \times \text{df['Значение'][1]}) / 3600 \rceil $$
    *   Итоговое время на входной контроль всей партии с учетом минимума (`t_incoming_control_all_hours`):
        Если  ` (t_{\text{incoming\_control\_base\_all\_hours}} \times 3600) < \text{df['Значение'][4]} `:
        $$ t_{\text{incoming\_control\_all\_hours}} = \lceil \text{df['Значение'][4]} / 3600 \rceil $$
        Иначе:
        $$ t_{\text{incoming\_control\_all\_hours}} = t_{\text{incoming\_control\_base\_all\_hours}} $$
    *   Стоимость входного контроля всей партии (`cost_incoming_control_all`):
        $$ \text{cost\_incoming\_control\_all} = t_{\text{incoming\_control\_all\_hours}} \times \text{df2['Стоимость, руб/ч'][19]} $$
    *   Время на входной контроль 1 ПУ (`t_incoming_control_pc_seconds`):
        $$ t_{\text{incoming\_control\_pc\_seconds}} = \lceil (t_{\text{incoming\_control\_all\_hours}} \times 3600) / \text{quantity} \rceil $$
    *   Стоимость входного контроля 1 ПУ (`cost_incoming_control_pc`):
        $$ \text{cost\_incoming\_control\_pc} = \lceil \text{cost\_incoming\_control\_all} / \text{quantity} \rceil $$

3.  **Выходной контроль:**
    *   Время на выходной контроль 1 ПУ в секундах (`t_outgoing_control_one_pc_seconds`):
        Определяется на основе `product_type`:
        *   Если `product_type == 1` (Серверная плата): `base_time = df['Значение'][2]`
        *   Если `product_type == 2` (Материнская плата): `base_time = df['Значение'][6]`
        *   Если `product_type == 3` (Маленькая плата): `base_time = df['Значение'][7]`
        *   Если `product_type == 4` (Средняя плата): `base_time = df['Значение'][8]`
        $$ t_{\text{outgoing\_control\_one\_pc\_seconds}} = \text{base\_time} + \text{df['Значение'][9]} $$
    *   Время на выходной контроль всей партии (`t_outgoing_control_all_hours`):
        $$ t_{\text{outgoing\_control\_all\_hours}} = \lceil (\text{quantity} \times t_{\text{outgoing\_control\_one\_pc\_seconds}}) / 3600 \rceil $$
    *   Стоимость выходного контроля всей партии (`cost_outgoing_control_all`):
        $$ \text{cost\_outgoing\_control\_all} = t_{\text{outgoing\_control\_all\_hours}} \times \text{df2['Стоимость, руб/ч'][21]} $$
    *   Время на выходной контроль 1 ПУ (`t_outgoing_control_pc_seconds`):
        $$ t_{\text{outgoing\_control\_pc\_seconds}} = \lceil (t_{\text{outgoing\_control\_all\_hours}} \times 3600) / \text{quantity} \rceil $$
        *(В JS это `time_pc3`, и оно фактически равно `t_outgoing_control_one_pc_seconds` после округления общего времени партии и деления)*
    *   Стоимость выходного контроля 1 ПУ (`cost_outgoing_control_pc`):
        $$ \text{cost\_outgoing\_control\_pc} = \lceil \text{cost\_outgoing\_control\_all} / \text{quantity} \rceil $$

4.  **Отгрузка:**
    *   Время на отгрузку всей партии (`t_shipment_all_hours`):
        $$ t_{\text{shipment\_all\_hours}} = \lceil (\text{quantity} \times \text{df['Значение'][3]}) / 3600 \rceil $$
    *   Стоимость отгрузки всей партии (`cost_shipment_all`):
        $$ \text{cost\_shipment\_all} = t_{\text{shipment\_all\_hours}} \times \text{df2['Стоимость, руб/ч'][22]} $$
    *   Время на отгрузку 1 ПУ (`t_shipment_pc_seconds`):
        $$ t_{\text{shipment\_pc\_seconds}} = \lceil (t_{\text{shipment\_all\_hours}} \times 3600) / \text{quantity} \rceil $$
    *   Стоимость отгрузки 1 ПУ (`cost_shipment_pc`):
        $$ \text{cost\_shipment\_pc} = \lceil \text{cost\_shipment\_all} / \text{quantity} \rceil $$

5.  **Итоговые значения:**
    *   Общее время на комплектацию всей партии (`t_all_comp_hours`):
        $$ t_{\text{all\_comp\_hours}} = t_{\text{acceptance\_all\_hours}} + t_{\text{incoming\_control\_all\_hours}} + t_{\text{outgoing\_control\_all\_hours}} + t_{\text{shipment\_all\_hours}} $$
    *   Общая стоимость комплектации всей партии (`cost_all_comp`):
        $$ \text{cost\_all\_comp} = \text{cost\_acceptance\_all} + \text{cost\_incoming\_control\_all} + \text{cost\_outgoing\_control\_all} + \text{cost\_shipment\_all} $$
    *   Общее время на комплектацию 1 ПУ (`t_pc_comp_seconds`):
        $$ t_{\text{pc\_comp\_seconds}} = \lceil (t_{\text{all\_comp\_hours}} \times 3600) / \text{quantity} \rceil $$
        *(Также можно получить суммированием `t_acceptance_pc_seconds`, `t_incoming_control_pc_seconds`, `t_outgoing_control_pc_seconds`, `t_shipment_pc_seconds`, но в JS итоговое время на ПУ считается из общего времени партии)*
    *   Общая стоимость комплектации 1 ПУ (`cost_pc_comp`):
        $$ \text{cost\_pc\_comp} = \lceil \text{cost\_all\_comp} / \text{quantity} \rceil $$

Эти итоговые значения `cost_all_comp` и `cost_pc_comp` отображаются на странице как "Итоговая стоимость всей партии" и "Итоговая стоимость 1 ПУ" соответственно.

# 4. THT монтаж (/tht)

На этой странице рассчитывается время и стоимость селективной пайки THT компонентов. Расчеты учитывают количество сторон пайки, способ ввода данных (ручной или симуляция), количество и типы компонентов, а также затраты на переналадку, ремонт и контроль. Расчеты производятся в JavaScript-функции `THT_amount()` в шаблоне `THT.html`.

**Входные параметры (из сессии `/home` и `/second`):**

*   `quantity`: Общее количество ПУ (плат) в партии (`session['home_form']['field3']`).
*   `multi_num`: Общее количество МЗ в партии (`session['second_form']['multi_num']`).
*   `pc_in_mz`: Количество плат в одной МЗ (`session['second_form']['pc']`).
*   `prev_production_status`: Производилось ли изделие ранее ( `1` - да, `2` - нет, из `session['second_form']['prev']`), влияет на коэффициент переналадки и процент брака.

**Входные параметры (со страницы `/tht`):**

*   `THT_active`: Чекбокс "Выполнять селективную пайку THT?" (поле `THT`). Если не отмечен, расчеты не производятся.
*   `num_sides`: Количество сторон для пайки (radio-кнопки `THT_sides`, значения `1` или `2`).
*   **Для Первой стороны (Primary / S1):**
    *   `calc_type_S1`: Способ расчета времени (radio-кнопки `THT_type`):
        *   `2` (Ручной ввод): Поля `points` (компоненты до 10 рядов), `points_2` (компоненты >10 рядов), `DDR` (DDR-разъемы), `PCI` (PCI-разъемы).
        *   `3` (Данные симуляции): Поле `sim_multi` (время на пайку 1 МЗ, с).
*   **Для Второй стороны (Secondary / S2), если `num_sides == 2`:**
    *   `calc_type_S2`: Способ расчета времени (radio-кнопки `THT_type2`):
        *   `2` (Ручной ввод): Поля `points2`, `points2_2`, `DDR2`, `PCI2`.
        *   `3` (Данные симуляции): Поле `sim_multi2` (время на пайку 1 МЗ, с).

**Константы из файлов данных:**

*   `data/THT.csv` (загружается в `df`):
    *   `df['Значение'][0]`: Общий поправочный коэффициент времени селективной пайки.
    *   `df['Значение'][1]`: Время пайки 1 DDR-разъёма, с/компонент.
    *   `df['Значение'][2]`: Время пайки 1 PCI-разъёма, с/компонент.
    *   `df['Значение'][3]`: Базовое время переналадки на 1 сторону, с.
    *   `df['Значение'][4]`: Дополнительное время на пайку на 1 МЗ (помимо времени на компоненты), с/МЗ.
    *   `df['Значение'][5]`: Время пайки 1 компонента "до 10 рядов точек", с/компонент.
    *   `df['Значение'][6]`: Коэффициент снижения времени переналадки, если `prev_production_status == 1`
    *   `df['Значение'][7]`: Процент брака для ремонта (если `prev_production_status == 1`).
    *   `df['Значение'][8]`: Процент брака для ремонта (если `prev_production_status == 2`).
    *   `df['Значение'][9]`: Норматив времени на ремонт 1 брака (относительно `quantity`), с.
    *   `df['Значение'][10]`: Норматив времени на контроль 1 брака (относительно `quantity`), с.
    *   `df['Значение'][11]`: Время пайки 1 компонента "более 10 рядов точек", с/компонент.
    *   *Примечание по `df['Значение'][11]` в JS:* В коде `THT_amount` при ручном расчете времени пайки МЗ к суммарному времени компонентов (`t_components_S1_seconds * pc_in_mz`) добавляется `pc_in_mz * parseFloat({{df['Значение'][11]}})`. Это выглядит как возможное ошибочное использование константы времени пайки компонента >10 рядов вместо предполагаемой базовой константы времени на МЗ при ручном вводе. Для целей этой документации, будем считать, что это отдельное время, добавляемое на каждую плату в МЗ, если есть хотя бы один компонент для ручного ввода (`time_per_pc_in_mz_manual_base = df['Значение'][11]`).
*   `data/variables.csv` (загружается в `df2`):
    *   `df2['Стоимость, руб/ч'][2]`: Стоимость часа работы установки селективной пайки.
    *   `df2['Стоимость, руб/ч'][3]`: Стоимость часа работы наладчика селективной пайки.
    *   `df2['Стоимость, руб/ч'][8]`: Стоимость часа работы ремонтника.
    *   `df2['Стоимость, руб/ч'][9]`: Стоимость часа работы оператора набивки THT компонентов.
    *   `df2['Стоимость, руб/ч'][21]`: Стоимость часа работы контролера.

**Расчеты (в `THT.html` - функция `THT_amount()`):**

Если чекбокс `THT_active` не отмечен, все поля на странице отображают "-".

1.  **Определение коэффициента переналадки (`setup_koef`):**
    *   Если `prev_production_status == 1`: `setup_koef = 1 - df['Значение'][6]`
    *   Иначе (`prev_production_status == 2`): `setup_koef = 1`

2.  **Расчет для Первой стороны (S1):**
    *   **Время пайки 1 МЗ (`t_soldering_mz_S1_seconds`):**
        *   Если `calc_type_S1 == 2` (Ручной ввод):
            `t_components_one_pc_S1_seconds = points_S1_cat1 * df['Значение'][5] + points_S1_cat2 * df['Значение'][11] + num_DDR_S1 * df['Значение'][1] + num_PCI_S1 * df['Значение'][2]`
            `base_mz_time_manual_S1 = 0`
            Если `(points_S1_cat1 + points_S1_cat2 + num_DDR_S1 + num_PCI_S1) > 0`, то `base_mz_time_manual_S1 = pc_in_mz * df['Значение'][11]` (см. примечание выше)
            `t_soldering_mz_S1_seconds = ceil(t_components_one_pc_S1_seconds * pc_in_mz + base_mz_time_manual_S1)`
        *   Если `calc_type_S1 == 3` (Симуляция):
            `t_soldering_mz_S1_seconds = sim_time_mz_S1`
    *   **Скорректированное время пайки 1 МЗ с коэффициентами (`t_soldering_mz_S1_adj_seconds`):**
        `t_soldering_mz_S1_adj_seconds = (t_soldering_mz_S1_seconds + df['Значение'][4]) * df['Значение'][0]`
    *   **Время пайки (производственное) партии для S1 (`t_prod_S1_hours`):**
        `t_prod_S1_hours = ceil((t_soldering_mz_S1_adj_seconds * multi_num / 2) / 3600)` (Деление на 2 из-за двух машин)
    *   **Стоимость пайки партии для S1 (`cost_prod_S1`):**
        `cost_prod_S1 = ceil(t_prod_S1_hours * df2['Стоимость, руб/ч'][2])`
    *   **Стоимость "набивки" (оператора) партии для S1 (`cost_stuffing_S1`):**
        `cost_stuffing_S1 = ceil(t_prod_S1_hours * df2['Стоимость, руб/ч'][9])`
    *   **Время переналадки партии для S1 (`t_setup_S1_hours`):**
        `t_setup_S1_hours = ceil((df['Значение'][3] * setup_koef) / 3600)`
    *   **Стоимость переналадки партии для S1 (`cost_setup_S1`):**
        `cost_setup_S1 = ceil(t_setup_S1_hours * df2['Стоимость, руб/ч'][3])`

3.  **Расчет для Второй стороны (S2), если `num_sides == 2`:**
    Аналогично пункту 2, но с использованием входных данных и переменных для S2 (`calc_type_S2`, `points2`, `sim_multi2` и т.д.). Получаем `t_prod_S2_hours`, `cost_prod_S2`, `cost_stuffing_S2`, `t_setup_S2_hours`, `cost_setup_S2`.
    Если `num_sides == 1`, все значения для S2 равны 0.

4.  **Расчет времени и стоимости ремонта:**
    *   Определение процента брака (`defect_rate`):
        Если `prev_production_status == 1`: `defect_rate = df["Значение"][7]`
        Иначе: `defect_rate = df["Значение"][8]`
    *   Количество изделий на ремонт (`num_for_repair = defect_rate * quantity`)
    *   Время на ремонт всей партии (`t_repair_all_hours`):
        $$ t_{\text{repair\_all\_hours}} = \lceil (\text{num\_for\_repair} \times \text{df["Значение"][9]} / 100) / 3600 \rceil $$
    *   Стоимость ремонта всей партии (`cost_repair_all`):
        $$ \text{cost\_repair\_all} = \lceil t_{\text{repair\_all\_hours}} \times \text{df2['Стоимость, руб/ч'][8]) \rceil $$

5.  **Расчет времени и стоимости контроля ремонта:**
    *   Время на контроль ремонта всей партии (`t_control_repair_all_hours`):
        $$ t_{\text{control\_repair\_all\_hours}} = \lceil (\text{num\_for\_repair} \times \text{df["Значение"][10]} / 100) / 3600 \rceil $$
    *   Стоимость контроля ремонта всей партии (`cost_control_repair_all`):
        $$ \text{cost\_control\_repair\_all} = \lceil t_{\text{control\_repair\_all\_hours}} \times \text{df2['Стоимость, руб/ч'][21]} \rceil $$

6.  **Итоговые время и стоимость на всю партию:**
    *   **Общее время (`t_all_THT_hours`):**
        $$ t_{\text{all\_THT\_hours}} = t_{\text{prod\_S1\_hours}} + t_{\text{setup\_S1\_hours}} + t_{\text{prod\_S2\_hours}} + t_{\text{setup\_S2\_hours}} + t_{\text{repair\_all\_hours}} + t_{\text{control\_repair\_all\_hours}} $$
        *(Примечание: в JS итоговые суммы для ПУ и партии показываются отдельно по категориям: "набивка", "сборка" (пайка), "переналадка". Здесь для `t_all` приведена общая сумма производственного времени)*
    *   **Общая стоимость (`cost_all_THT`):**
        $$ \text{cost\_all\_THT} = \text{cost\_prod\_S1} + \text{cost\_stuffing\_S1} + \text{cost\_setup\_S1} + \text{cost\_prod\_S2} + \text{cost\_stuffing\_S2} + \text{cost\_setup\_S2} + \text{cost\_repair\_all} + \text{cost\_control\_repair\_all} $$ 

7.  **Итоговые время и стоимость на 1 ПУ:**
    Рассчитываются делением соответствующих общих значений на `quantity` (с округлением вверх для стоимости и времени на ПУ в секундах).
    *   `t_pc_THT_seconds = ceil(t_all_THT_hours_for_pu * 3600 / quantity)` (где `t_all_THT_hours_for_pu` - это сумма времен пайки, набивки и переналадки для S1 и S2, без ремонта)
    *   `cost_pc_THT = ceil(cost_all_THT / quantity)`

На странице также отображается детализация времени и стоимости по сторонам (Primary/Secondary) для набивки, сборки (пайки) и переналадки, а также отдельно по ПУ.

# 5. Волновая пайка (/wave)

На странице рассчитывается время и стоимость волновой пайки, включая работу установки, операторов набивки, а также ремонт и контроль качества. Расчеты производятся в JavaScript-функции `wave_amount()` в шаблоне `Wave.html`.

**Входные параметры (из сессии `/home` и `/second`):**

*   `quantity`: Общее количество ПУ (плат) в партии (`session['home_form']['field3']`).
*   `multi_num`: Общее количество МЗ в партии (`session['second_form']['multi_num']`).
*   `pc_in_mz`: Количество плат в одной МЗ (`session['second_form']['pc']`).
*   `prev_production_status`: Производилось ли изделие ранее (`1` - да, `2` - нет, из `session['second_form']['prev']`), влияет на процент брака.

**Входные параметры (со страницы `/wave`):**

*   `Wave_active`: Чекбокс \"Выполнять волновую пайку?\" (поле `Wave`). Если не отмечен, расчеты не производятся.
*   `num_wave_components_pp`: Количество компонентов для волновой пайки на 1 ПУ (поле `Wave_num`).
*   `num_fixtures`: Количество используемых оснасток (поле `Wave_eq_num`).
*   `is_motherboard_or_server`: Чекбокс \"Это материнская или серверная плата?\" (поле `Wave_type`).
*   `use_simulation`: Чекбокс \"Использовать симуляцию?\" (поле `Wave_sim`).
*   `sim_time_pp_seconds`: Время по симуляции на 1 плату, с (поле `Wave_sim_v`), если `use_simulation` активен.

**Константы из файлов данных:**

*   `data/Wave.csv` (загружается в `df`):
    *   `df['Значение'][0]`: Время окончания пайки (дополнительное время в конце цикла на 1 МЗ), с (`t_end_cycle_mz`).
    *   `df['Значение'][1]`: Коэффициент, используемый с `prev_production_status == 1` (в JS `prev_koef = 1 - df['Значение'][1]`). Не используется в расчете времени цикла в текущей реализации JS, но влияет на выбор процента брака.
    *   `df['Значение'][3]`: Процент брака для ремонта (если `prev_production_status == 2` - новая продукция).
    *   `df['Значение'][4]`: Процент брака для ремонта (если `prev_production_status == 1` - производилось ранее).
    *   `df['Значение'][5]`: Норматив времени на ремонт 1 брака от партии, с.
    *   `df['Значение'][6]`: Количество операторов/рабочих мест (`n_operators`)
    *   `df['Значение'][7]`: Коэффициент производительности `k` для плат, не являющихся материнскими/серверными. Если плата материнская/серверная, `k=1`.
    *   `df['Значение'][8]`: Время на пайку 1 компонента при волновой пайке, с/компонент (`t_component_wave`).
    *   `df['Значение'][9]`: Базовое время на АОИ на 1 МЗ, с (`t_aoi_base_mz`). В коде JS умножается на 2: `t_aoi_mz = 2 * df['Значение'][9]`.
    *   `df['Значение'][10]`: Базовое время процесса волновой пайки на 1 МЗ, с (`t_wave_process_base_mz`). Делится на коэффициент `k`.
    *   `df['Значение'][11]`: Общий поправочный коэффициент времени производственного процесса волновой пайки.
*   `data/variables.csv` (загружается в `df2`):
    *   `df2['Стоимость, руб/ч'][4]`: Стоимость часа работы установки волновой пайки.
    *   `df2['Стоимость, руб/ч'][8]`: Стоимость часа работы ремонтника.
    *   `df2['Стоимость, руб/ч'][9]`: Стоимость часа работы оператора набивки (для волновой пайки).
    *   `df2['Стоимость, руб/ч'][21]`: Стоимость часа работы контролера.

**Расчеты (в `Wave.html` - функция `wave_amount()`):**

Если чекбокс `Wave_active` не отмечен, все поля на странице отображают "-".

1.  **Определение коэффициента `k` для типа платы:**
    *   Если `is_motherboard_or_server` отмечен: `k = 1`
    *   Иначе: `k = df['Значение'][7]`

2.  **Расчет времени цикла на 1 МЗ (`CycleTime_mz`) и времени такта (`dt_mz`):**
    *   Количество компонентов на МЗ: `N_comp_mz = num_wave_components_pp * pc_in_mz`
    *   Время АОИ на МЗ: `t_aoi_mz = 2 * df['Значение'][9]`
    *   Время процесса волновой пайки на МЗ: `t_wave_process_mz = df['Значение'][10] / k`
    *   Время окончания цикла на МЗ: `t_end_cycle_mz = df['Значение'][0]`
    *   Количество операторов: `n_operators = df['Значение'][6]`
    *   Время такта, если ограничено операторами: `dt_operators_limit_mz = (N_comp_mz * df['Значение'][8] + t_aoi_mz) / n_operators`
    *   Полное время цикла на 1 МЗ: `CycleTime_mz = N_comp_mz * df['Значение'][8] + t_aoi_mz + t_wave_process_mz + t_end_cycle_mz`
    *   Необходимое количество оснасток для такта `dt_operators_limit_mz`: `n_fixtures_for_operator_limit = CycleTime_mz / dt_operators_limit_mz`
    *   **Итоговое время такта на МЗ (`dt_final_mz`):**
        Если `(num_fixtures - n_operators <= 0)` ИЛИ `(n_fixtures_for_operator_limit > num_fixtures)`:
        `dt_final_mz = CycleTime_mz / num_fixtures` (Ограничено количеством оснасток).
        Иначе:
        `dt_final_mz = dt_operators_limit_mz` (Ограничено операторами).

3.  **Общее производственное время партии (`t_prod_all_hours`):**
    *   Если `use_simulation` НЕ отмечен:
        `t_prod_all_raw_hours = (dt_final_mz * multi_num + CycleTime_mz) / 3600`
        `t_prod_all_hours = ceil(t_prod_all_raw_hours * df['Значение'][11])` (Применение общего поправочного коэффициента и округление).
    *   Если `use_simulation` отмечен:
        `t_prod_all_hours = ceil(sim_time_pp_seconds * quantity / 3600)` (Округление).

4.  **Стоимость производственных операций партии:**
    *   Стоимость работы установки волновой пайки: `cost_wave_machine_all = ceil(t_prod_all_hours * df2['Стоимость, руб/ч'][4])`.
    *   Стоимость работы операторов набивки: `cost_operators_all = ceil(t_prod_all_hours * df2['Стоимость, руб/ч'][9])`.

5.  **Расчет времени и стоимости ремонта:**
    *   Процент брака (`defect_rate`):
        Если `prev_production_status == 1`: `defect_rate = df["Значение"][4]` (брак для производившейся ранее продукции).
        Иначе (`prev_production_status == 2`): `defect_rate = df["Значение"][3]` (брак для новой продукции).
    *   Количество изделий на ремонт: `num_for_repair = defect_rate * quantity`.
    *   Время на ремонт всей партии: `t_repair_all_hours = ceil((num_for_repair * df["Значение"][5] / 100) / 3600)`.
    *   Стоимость ремонта всей партии: `cost_repair_all = ceil(t_repair_all_hours * df2['Стоимость, руб/ч'][8])`.

6.  **Расчет времени и стоимости контроля ремонта:**
    *   Время на контроль ремонта всей партии: `t_control_repair_all_hours = ceil((num_for_repair * df["Значение"][6] / 100) / 3600)` (Используется `df["Значение"][6]`, которое также `n_operators`).
    *   Стоимость контроля ремонта всей партии: `cost_control_repair_all = ceil(t_control_repair_all_hours * df2['Стоимость, руб/ч'][21])`.

7.  **Итоговые время и стоимость на всю партию:**
    *   **Общее время (`t_all_wave_display_hours`):** В JS `time_all` и `time_all_p` фактически равны `t_prod_all_hours`. Для общего времени процесса с ремонтом: $$ t_{\text{all\_wave\_total\_hours}} = t_{\text{prod\_all\_hours}} + t_{\text{repair\_all\_hours}} + t_{\text{control\_repair\_all\_hours}} $$
    *   **Общая стоимость (`cost_all_wave`):**
        $$ \text{cost\_all\_wave} = \text{cost\_wave\_machine\_all} + \text{cost\_operators\_all} + \text{cost\_repair\_all} + \text{cost\_control\_repair\_all} $$

8.  **Итоговые время и стоимость на 1 ПУ:**
    Рассчитываются делением соответствующих общих значений на `quantity` (с округлением вверх для стоимости и времени на ПУ в секундах).
    *   `t_pc_wave_display_seconds = ceil(t_prod_all_hours * 3600 / quantity)` (Время производственное на 1 ПУ)
    *   `cost_pc_wave = ceil(cost_all_wave / quantity)`

На странице также отображается детализация времени и стоимости для "набивки" (операторы) и "сборки" (работа установки), а также отдельно ремонт и контроль.

# 6. Лакировка HRL (/HRL)

На странице рассчитывается время и стоимость селективной лакировки с использованием установки HRL, включая производственное время, время переналадки, а также ремонт и контроль качества. Расчеты производятся в JavaScript-функции `HRL_amount()` в шаблоне `HRL.html`.

**Входные параметры (из сессии `/home` и `/second`):**

*   `quantity`: Общее количество ПУ (плат) в партии (`session['home_form']['field3']`).
*   `multi_num`: Общее количество МЗ в партии (`session['second_form']['multi_num']`).
*   `width_mz`: Ширина МЗ, мм (`session['second_form']['width']`).
*   `length_mz`: Длина МЗ, мм (`session['second_form']['length']`).
*   `prev_production_status`: Производилось ли изделие ранее (`1` - да, `2` - нет, из `session['second_form']['prev']`), влияет на коэффициент переналадки и процент брака.

**Входные параметры (со страницы `/HRL`):**

*   `HRL_active`: Чекбокс \"Выполнять селективную лакировку HRL?\" (поле `HRL`). Если не отмечен, расчеты не производятся.
*   `num_sides_hrl`: Количество сторон для лакировки (radio-кнопки `HRL_type`, значения `1` - односторонняя, `2` - двусторонняя).

**Константы из файлов данных:**

*   `data/HRL.csv` (загружается в `df`):
    *   `df['Значение'][0]`: Производительность установки HRL, мм²/проход (площадь, покрываемая за один проход). Используется как `area_coverage_per_pass`.
    *   `df['Значение'][1]`: Время одного прохода установки HRL, с/проход (`time_per_pass`).
    *   `df['Значение'][2]`: Коэффициент снижения времени переналадки, если `prev_production_status == 1` (например, 0.3 означает снижение на 30%).
    *   `df['Значение'][3]`: Базовое время переналадки на 1 сторону, с (`base_setup_time_per_side`).
    *   `df['Значение'][4]`: Процент брака для ремонта (если `prev_production_status == 2` - новая продукция).
    *   `df['Значение'][5]`: Процент брака для ремонта (если `prev_production_status == 1` - производилось ранее).
    *   `df['Значение'][6]`: Норматив времени на ремонт 1 шт, с.
    *   `df['Значение'][7]`: Норматив времени на контроль 1 шт, с.
*   `data/variables.csv` (загружается в `df2`):
    *   `df2['Стоимость, руб/ч'][6]`: Стоимость часа работы установки HRL (лакировка).
    *   `df2['Стоимость, руб/ч'][7]`: Стоимость часа работы наладчика HRL (переналадка).
    *   `df2['Стоимость, руб/ч'][8]`: Стоимость часа работы ремонтника.
    *   `df2['Стоимость, руб/ч'][21]`: Стоимость часа работы контролера.

**Расчеты (в `HRL.html` - функция `HRL_amount()`):**

Если чекбокс `HRL_active` не отмечен, все поля на странице отображают "-".

1.  **Определение коэффициента переналадки (`prev_koef_setup`):**
    *   Если `prev_production_status == 1`: `prev_koef_setup = 1 - df['Значение'][2]`
    *   Иначе (`prev_production_status == 2`): `prev_koef_setup = 1`

2.  **Определение количества обрабатываемых сторон (`sides_to_process`):**
    *   Если `num_sides_hrl == 1`: `sides_to_process = 1`
    *   Если `num_sides_hrl == 2`: `sides_to_process = 2`

3.  **Расчет времени и стоимости лакировки (производственное):**
    *   Площадь МЗ: `area_mz = ceil(width_mz * length_mz)`
    *   Количество проходов на 1 МЗ на 1 сторону: `num_passes_mz_one_side = ceil(area_mz / df['Значение'][0])`
    *   Общее количество проходов для партии: `total_passes_batch = multi_num * sides_to_process * num_passes_mz_one_side`
    *   Общее время лакировки партии, часы (`t_lacquering_all_hours`):
        $$ t_{\text{lacquering\_all\_hours}} = \lceil (\text{total\_passes\_batch} \times \text{df['Значение'][1]}) / 3600 \rceil $$
    *   Стоимость лакировки партии (`cost_lacquering_all`):
        $$ \text{cost\_lacquering\_all} = \lceil t_{\text{lacquering\_all\_hours}} \times \text{df2['Стоимость, руб/ч'][6]} \rceil $$

4.  **Расчет времени и стоимости переналадки:**
    *   Общее время переналадки партии, секунды (`t_setup_all_seconds`):
        $$ t_{\text{setup\_all\_seconds}} = \text{df['Значение'][3]} \times \text{sides\_to\_process} \times \text{prev\_koef\_setup} $$
    *   Общее время переналадки партии, часы (`t_setup_all_hours`):
        $$ t_{\text{setup\_all\_hours}} = \lceil t_{\text{setup\_all\_seconds}} / 3600 \rceil $$
    *   Стоимость переналадки партии (`cost_setup_all`):
        $$ \text{cost\_setup\_all} = \lceil (t_{\text{setup\_all\_seconds}} \times \text{df2['Стоимость, руб/ч'][7]}) / 3600 \rceil $$

5.  **Расчет времени и стоимости ремонта:**
    *   Процент брака (`defect_rate`):
        Если `prev_production_status == 1`: `defect_rate = df["Значение"][5]` (брак для производившейся ранее продукции)
        Иначе (`prev_production_status == 2`): `defect_rate = df["Значение"][4]` (брак для новой продукции)
    *   Количество изделий на ремонт: `num_for_repair = defect_rate * quantity`
    *   Время на ремонт всей партии (`t_repair_all_hours`):
        $$ t_{\text{repair\_all\_hours}} = \lceil (\text{num\_for\_repair} \times \text{df["Значение"][6]} / 100) / 3600 \rceil $$
    *   Стоимость ремонта всей партии (`cost_repair_all`):
        $$ \text{cost\_repair\_all} = \lceil t_{\text{repair\_all\_hours}} \times \text{df2['Стоимость, руб/ч'][8]} \rceil $$

6.  **Расчет времени и стоимости контроля ремонта:**
    *   Время на контроль ремонта всей партии (`t_control_repair_all_hours`):
        $$ t_{\text{control\_repair\_all\_hours}} = \lceil (\text{num\_for\_repair} \times \text{df["Значение"][7]} / 100) / 3600 \rceil $$
    *   Стоимость контроля ремонта всей партии (`cost_control_repair_all`):
        $$ \text{cost\_control\_repair\_all} = \lceil t_{\text{control\_repair\_all\_hours}} \times \text{df2['Стоимость, руб/ч'][21]} \rceil $$

7.  **Итоговые время и стоимость на всю партию:**
    *   **Общее время (`t_all_HRL_total_hours`):**
        $$ t_{\text{all\_HRL\_total\_hours}} = t_{\text{lacquering\_all\_hours}} + t_{\text{setup\_all\_hours}} + t_{\text{repair\_all\_hours}} + t_{\text{control\_repair\_all\_hours}} $$
    *   **Общая стоимость (`cost_all_HRL`):**
        $$ \text{cost\_all\_HRL} = \text{cost\_lacquering\_all} + \text{cost\_setup\_all} + \text{cost\_repair\_all} + \text{cost\_control\_repair\_all} $$

8.  **Итоговые время и стоимость на 1 ПУ:**
    *   Время на 1 ПУ (лакировка + переналадка), секунды:
        `t_pc_HRL_main_seconds = ceil((t_lacquering_all_hours + t_setup_all_hours) * 3600 / quantity)`
    *   Стоимость на 1 ПУ (общая):
        `cost_pc_HRL = ceil(cost_all_HRL / quantity)`

На странице также отображается детализация времени и стоимости для лакировки, переналадки, ремонта и контроля.

# 7. Ручной монтаж (/hand)

На этой странице рассчитывается время и стоимость ручного монтажа (пайки) компонентов, а также связанного с этим контроля качества. Расчеты производятся в JavaScript-функции `hand_amount()` в шаблоне `Hand.html`.

**Входные параметры (из сессии `/home`):**

*   `quantity`: Общее количество ПУ (плат) в партии (`session['home_form']['field3']`).

**Входные параметры (со страницы `/hand`):**

*   `Hand_active`: Чекбокс \"Выполнять ручной монтаж?\" (поле `Hand`). Если не отмечен, расчеты не производятся.
*   `num_soldering_points_pp`: Количество точек пайки на 1 ПУ (поле `Hand_num`).

**Константы из файлов данных:**

*   `data/Hand.csv` (загружается в `df`):
    *   `df['Значение'][0]`: Время на пайку одной точки, с/точка (`time_per_soldering_point`).
    *   `df['Значение'][1]`: Базовое время на подготовку/завершение для всей партии (переналадка), с (`base_setup_time_batch`).
    *   `df['Значение'][2]`: Время на контроль одной точки пайки, с/точка (`time_per_control_point`).
*   `data/variables.csv` (загружается в `df2`):
    *   `df2['Стоимость, руб/ч'][8]`: Стоимость часа работы для ручного монтажа (пайки).
    *   `df2['Стоимость, руб/ч'][21]`: Стоимость часа работы контролера.

**Расчеты (в `Hand.html` - функция `hand_amount()`):**

Если чекбокс `Hand_active` не отмечен, все поля на странице отображают "-".

1.  **Расчет времени и стоимости пайки:**
    *   Базовое время пайки на 1 ПУ (без учета переналадки на партию), секунды:
        `t_soldering_pc_base_seconds = num_soldering_points_pp * df['Значение'][0]`
    *   Общее время пайки партии (включая переналадку), часы (`t_soldering_all_hours_with_setup`):
        $$ t_{\text{soldering\_all\_hours\_with\_setup}} = \lceil ( (t_{\text{soldering\_pc\_base\_seconds}} \times \text{quantity}) + \text{df['Значение'][1]} ) / 3600 \rceil $$
    *   Скорректированное время пайки на 1 ПУ (после распределения общего времени партии), секунды (`t_soldering_pc_final_seconds`):
        $$ t_{\text{soldering\_pc\_final\_seconds}} = \lceil (t_{\text{soldering\_all\_hours\_with\_setup}} \times 3600) / \text{quantity} \rceil $$
    *   Стоимость пайки партии (`cost_soldering_all`):
        $$ \text{cost\_soldering\_all} = \lceil t_{\text{soldering\_all\_hours\_with\_setup}} \times \text{df2['Стоимость, руб/ч'][8]} \rceil $$
    *   Стоимость пайки на 1 ПУ (`cost_soldering_pc_display`):
        $$ \text{cost\_soldering\_pc\_display} = \lceil \text{cost\_soldering\_all} / \text{quantity} \rceil $$

2.  **Расчет времени и стоимости контроля:**
    *   Общее время контроля партии, часы (`t_control_all_hours`):
        $$ t_{\text{control\_all\_hours}} = \lceil (\text{quantity} \times \text{df['Значение'][2]} \times \text{num_soldering_points_pp}) / 3600 \rceil $$
    *   Стоимость контроля партии (`cost_control_all`):
        $$ \text{cost\_control\_all} = \lceil t_{\text{control\_all\_hours}} \times \text{df2['Стоимость, руб/ч'][21]} \rceil $$

3.  **Итоговые время и стоимость на всю партию:**
    *   **Общее время (`t_all_hand_total_hours`):** (В JS итоговое время не суммируется явно для отображения, но можно рассчитать так):
        $$ t_{\text{all\_hand\_total\_hours}} = t_{\text{soldering\_all\_hours\_with\_setup}} + t_{\text{control\_all\_hours}} $$
    *   **Общая стоимость (`cost_all_hand_final`):**
        $$ \text{cost\_all\_hand\_final} = \text{cost\_soldering\_all} + \text{cost\_control\_all} $$

4.  **Итоговые время и стоимость на 1 ПУ (для отображения):**
    *   Время пайки на 1 ПУ: `t_soldering_pc_final_seconds` (отображается как `time_pc`).
    *   Стоимость ручного монтажа (пайка + контроль) на 1 ПУ: `cost_pc_hand_final = ceil(cost_all_hand_final / quantity)` (отображается как `money_pc_f`).

На странице отображаются детализированные значения для пайки и контроля отдельно.

# 8. Тестирование (/test)

На этой странице рассчитывается суммарное время и стоимость для операций тестирования и прошивки (микросхем и самих ПУ). Расчеты производятся в JavaScript, в основном в функции `test_amount()` и вспомогательных `firmware_amount()`, `testing_amount()`, `firmware_m_amount()` в шаблоне `Test.html`.

**Входные параметры (из сессии `/home`):**

*   `quantity`: Общее количество ПУ (плат) в партии (`session['home_form']['field3']`).

**Входные параметры (со страницы `/test`):**

*   `Test_active`: Главный чекбокс \"Выполнять тестирование?\" (поле `Test`). Если не отмечен, все расчеты обнуляются.\\n*   **Прошивка микросхем:**\\n    *   `firmware_m_active`: Чекбокс \"Выполнять прошивку микросхем?\" (поле `firmware_m`).\\n    *   Динамическая таблица (`id=\\\"myTable\\\`): Каждая строка `i` содержит:\\n        *   `time_m_i`: Время прошивки i-й микросхемы, с (поле `time_i`).\\n        *   `num_m_i`: Количество i-х микросхем на 1 ПУ (поле `num_i`).\\n        *   `num_m_types`: Общее количество разных типов микросхем для прошивки (скрытое поле `rows`).\\n*   **Прошивка ПУ:**\\n    *   `firmware_pu_active`: Чекбокс \"Выполнять прошивку (ПУ)?\\\" (поле `firmware`).\\n    *   `time_firmware_pu_one`: Время на прошивку одного ПУ, с (поле `firmware_time`).\\n    *   `num_pu_in_firmware_simultaneously`: Количество ПУ, прошиваемых одновременно (поле `firmware_num`).\\n*   **Тестирование ПУ:**\\n    *   `testing_pu_active`: Чекбокс \"Выполнять тестирование (операция)?\\\" (поле `testing`).\\n    *   `testing_percentage`: Процент ПУ от партии, подвергаемый тестированию, % (поле `testing_proc`).\\n    *   `time_testing_pu_one`: Время на тестирование одного ПУ, с (поле `testing_time`).\\n    *   `num_pu_in_testing_simultaneously`: Количество ПУ, тестируемых одновременно (поле `testing_num`).\\n\\n**Константы из файлов данных:**\\n\\n*   `data/Test.csv` (загружается в `df`):\\n    *   `df[\\\'Значение\\\'][0]`: Время на подготовку программатора для одного типа микросхем, с (`setup_time_per_m_type`).\\n    *   `df[\\\'Значение\\\'][2]`: Поправочный коэффициент времени для прошивки ПУ (`koef_firmware_pu`).\\n    *   `df[\\\'Значение\\\'][3]`: Поправочный коэффициент времени для тестирования ПУ и для прошивки микросхем (`koef_testing_and_m_firmware`).\\n    *   `df[\\\'Значение\\\'][4]`: Количество микросхем, прошиваемых одновременно на одном программаторе (`num_m_simultaneously_on_programmer`).\\n*   `data/variables.csv` (загружается в `df2`):\\n    *   `df2[\\\'Стоимость, руб/ч\\\'][10]`: Единая стоимость часа работы для всех операций на этой странице.\\n\\n**Расчеты (в `Test.html`):**\\n\\nОбщая логика: суммируется время на 1 ПУ от каждой активной под-операции, затем это время используется для расчета общих показателей для партии.\\n\\n1.  **Время прошивки ПУ на 1 ПУ (`t_firmware_pu_pc_seconds`), если `firmware_pu_active`:**\\n    (Вычисляется в `firmware_amount()`)\\n    $$ t_{\\text{firmware\\_pu\\_pc\\_seconds}} = \\lceil (\\text{time\\_firmware\\_pu\\_one} / \\text{num\\_pu\\_in\\_firmware\\_simultaneously}) \\times \\text{df[\\\'Значение\\\'][2]} \\rceil $$\\n    Если неактивно, то 0.\\n\\n2.  **Время тестирования ПУ на 1 ПУ (`t_testing_pu_pc_seconds`), если `testing_pu_active`:**\\n    (Вычисляется в `testing_amount()`)\\n    $$ t_{\\text{testing\\_pu\\_pc\\_seconds}} = \\lceil (\\text{time\\_testing\\_pu\\_one} / \\text{num\\_pu\\_in\\_testing\\_simultaneously}) \\times (\\text{testing\\_percentage} / 100) \\times \\text{df[\\\'Значение\\\'][3]} \\rceil $$\\n    Если неактивно, то 0.\\n\\n3.  **Время прошивки микросхем на 1 ПУ (`t_firmware_m_pc_seconds`), если `firmware_m_active`:**\\n    (Вычисляется в `firmware_m_amount()`)\\n    Промежуточный расчет для каждого типа микросхемы `i` (от 0 до `num_m_types - 1`):\\n    $$ t_{\\text{per\\_m\\_type\\_i}} = \\lceil (\\text{time\\_m\\_i} \\times \\text{num\\_m\\_i}) / \\text{df[\\\'Значение\\\'][4]} \\rceil + \\text{df[\\\'Значение\\\'][0]} $$\\n    Суммарное время по всем типам микросхем до применения коэффициента:\\n    $$ \\text{sum\\_all\\_m\\_types} = \\sum_{i=0}^{\\text{num_m_types}-1} t_{\\text{per\\_m\\_type\\_i}} $$\\n    Итоговое время прошивки микросхем на 1 ПУ:\\n    $$ t_{\\text{firmware\\_m\\_pc\\_seconds}} = \\lceil \\text{sum\\_all\\_m\\_types} \\times \\text{df[\\\'Значение\\\'][3]} \\rceil $$\\n    Если неактивно, то 0.\\n\\n4.  **Суммарное время на 1 ПУ для всех активных операций (`t_total_pc_seconds`):**\\n    $$ t_{\\text{total\\_pc\\_seconds}} = t_{\\text{firmware\\_pu\\_pc\\_seconds}} + t_{\\text{testing\\_pu\\_pc\\_seconds}} + t_{\\text{firmware\\_m\\_pc\\_seconds}} $$\\n    Это значение отображается как `time_pc`.\\n\\n5.  **Общее время на всю партию (`t_total_all_hours`):**\\n    $$ t_{\\text{total\\_all\\_hours}} = \\lceil (t_{\\text{total\\_pc\\_seconds}} \\times \\text{quantity}) / 3600 \\rceil $$\\n    Отображается как `time_all`.\\n\\n6.  **Общая стоимость на всю партию (`cost_total_all`):**\\n    $$ \\text{cost\\_total\\_all} = \\lceil t_{\\text{total\\_all\\_hours}} \\times \\text{df2[\\\'Стоимость, руб/ч\\\'][10]} \\rceil $$\\n    Отображается как `money_all` и `money_all_f`.\\n\\n7.  **Стоимость на 1 ПУ (`cost_total_pc`):**\\n    $$ \\text{cost\\_total\\_pc} = \\lceil \\text{cost\\_total\\_all} / \\text{quantity} \\rceil $$\\n    Отображается как `money_pc` и `money_pc_f`.\\n\\nЕсли главный чекбокс `Test_active` не отмечен, все поля для отображения времени и стоимости (`time_pc`, `time_all`, `money_pc`, `money_all`, `money_pc_f`, `money_all_f`) показывают \\\"-\\\".

# 9. Отмывка (/clear)

На странице рассчитывается время и стоимость отмывки плат. Расчеты учитывают тип программы отмывки (укороченная/полная), количество плат в рамке, общее количество плат в партии, а также включает время на контроль качества.
Предварительные расчеты по вместимости плат в рамку отмывки производятся в Python (`calculations_money.py`), а окончательные расчеты времени и стоимости – в JavaScript-функции `multiply()` в шаблоне `Clear.html`.

**Входные параметры (из сессии `/home` и `/second`):**

*   `quantity`: Общее количество ПУ (плат) в партии (`session[\'home_form\'][\'field3\']`).
*   `width_mz`: Ширина МЗ, мм (`session[\'second_form\'][\'width\']`).
*   `length_mz`: Длина МЗ, мм (`session[\'second_form\'][\'length\']`).
*   `num_pu_width_mz`: Количество плат в ширину на МЗ (`session[\'second_form\'][\'width_num\']`).
*   `num_pu_length_mz`: Количество плат в длину на МЗ (`session[\'second_form\'][\'length_num\']`).

**Входные параметры (со страницы `/clear`):**

*   `Clear_active`: Чекбокс \"Выполнять отмывку?\" (поле `Clear`). Если не отмечен, расчеты не производятся.
*   `clear_program_type`: Тип программы отмывки (radio-кнопки `Clear_type`, значения `1` - Укороченная, `2` - Полная).

**Промежуточные расчеты (в `calculations_money.py` - функция `clear_calculations()`):**

Функция `clear_calculations(width_mz, length_mz, num_pu_width_mz, num_pu_length_mz, quantity, df_clear_csv)` определяет:

*   `frame_width = df_clear_csv[\'Значение\'][3]`: Ширина рамки отмывки.
*   `frame_length = df_clear_csv[\'Значение\'][2]`: Длина рамки отмывки.
*   `num_mz_fit_width = floor(frame_width / width_mz)`: Сколько МЗ помещается в ширину рамки.
*   `num_mz_fit_length = floor(frame_length / length_mz)`: Сколько МЗ помещается в длину рамки.
*   `num_mz_in_frame_calc = num_mz_fit_width * num_mz_fit_length`: Расчетное кол-во МЗ в рамке.
*   `num_pu_in_mz = num_pu_width_mz * num_pu_length_mz`: Кол-во плат в одной МЗ.
*   `num_pu_in_frame_calc = num_pu_in_mz * num_mz_in_frame_calc`: Расчетное кол-во плат в рамке.

Далее идет корректировка, если партия меньше одной загрузки рамки:
*   Если `quantity < num_pu_in_frame_calc`:
    *   `num_pu_in_frame_final = quantity`
    *   `num_mz_in_frame_final = ceil(quantity / num_pu_in_mz)`
*   Иначе:
    *   `num_pu_in_frame_final = num_pu_in_frame_calc`
    *   `num_mz_in_frame_final = num_mz_in_frame_calc`

Результат `[num_mz_in_frame_final, num_pu_in_mz, num_pu_in_frame_final]` передается в шаблон как `data`.

**Константы из файлов данных:**

*   `data/Clear.csv` (загружается в `df` в Python):
    *   `df[\'Значение\'][0]`: Время укороченной программы отмывки, мин/цикл (`time_short_program`).
    *   `df[\'Значение\'][1]`: Время полной программы отмывки, мин/цикл (`time_full_program`).
    *   `df[\'Значение\'][4]`: Общий поправочный коэффициент времени отмывки.
    *   `df[\'Значение\'][5]`: Время контроля на 1 МЗ, с (`control_time_per_mz`).
*   `data/variables.csv` (загружается в `df2` в Python):
    *   `df2[\'Стоимость, руб/ч\'][12]`: Стоимость часа работы установки отмывки.
    *   `df2[\'Стоимость, руб/ч\'][21]`: Стоимость часа работы контролера.

**Расчеты (в `Clear.html` - функция `multiply()`):**

Если чекбокс `Clear_active` не отмечен, все поля на странице отображают \"-\".

1.  **Определение времени программы на один цикл (`time_per_cycle_minutes`):**
    *   Если `clear_program_type == 1` (Укороченная): `time_per_cycle_minutes = df[\'Значение\'][0]`
    *   Если `clear_program_type == 2` (Полная): `time_per_cycle_minutes = df[\'Значение\'][1]`

2.  **Получение данных из Python:**
    *   `num_mz_in_frame = data[0]` (из `num_mz_in_frame_final`)
    *   `num_pu_in_frame = data[2]` (из `num_pu_in_frame_final`)

3.  **Расчет времени и стоимости отмывки:**
    *   Количество циклов отмывки: `num_cycles = ceil(quantity / num_pu_in_frame)` (если `num_pu_in_frame > 0`, иначе 0)
    *   Общее время отмывки партии, часы (`t_wash_all_hours`):
        $$ t_{\text{wash\_all\_hours}} = \lceil (\text{num\_cycles} \times \text{time\_per\_cycle\_minutes} \times \text{df[\'Значение\'][4]}) / 60 \rceil $$
    *   Стоимость отмывки партии (`cost_wash_all`):
        $$ \text{cost\_wash\_all} = \lceil t_{\text{wash\_all\_hours}} \times \text{df2[\'Стоимость, руб/ч\'][12]} \rceil $$

4.  **Расчет времени и стоимости контроля:**
    *   Количество плат в МЗ (из данных Python): `num_pu_in_mz_py = data[1]`.
    *   Общее количество МЗ для контроля (`total_mz_for_control`):
        Если `num_pu_in_mz_py > 0`: $$ \text{total\_mz\_for\_control} = \lceil \text{quantity} / \text{num_pu_in_mz_py} \rceil $$
        Иначе: `total_mz_for_control = 0`
    *   Общее время контроля партии, часы (`t_control_all_hours`):
        $$ t_{\text{control\_all\_hours}} = \lceil (\text{total\_mz\_for\_control} \times \text{df[\'Значение\'][5]}) / 3600 \rceil $$
    *   Стоимость контроля партии (`cost_control_all`):
        $$ \text{cost\_control\_all} = \lceil t_{\text{control\_all\_hours}} \times \text{df2[\'Стоимость, руб/ч\'][21]} \rceil $$

5.  **Итоговые время и стоимость на всю партию:**
    *   **Общее время (`t_all_clear_display_hours`):** В JS `time_all` и `time_all_p` равны `t_wash_all_hours`. Для общего времени процесса с контролем:
        $$ t_{\text{all\_clear\_total\_hours}} = t_{\text{wash\_all\_hours}} + t_{\text{control\_all\_hours}} $$ 
    *   **Общая стоимость (`cost_all_clear`):**
        $$ \text{cost\_all\_clear} = \text{cost\_wash\_all} + \text{cost\_control\_all} $$ 

6.  **Итоговые время и стоимость на 1 ПУ:**
    *   Время на 1 ПУ (только отмывка), секунды: `t_pc_clear_wash_seconds = ceil(t_wash_all_hours * 3600 / quantity)`
    *   Стоимость на 1 ПУ (общая): `cost_pc_clear = ceil(cost_all_clear / quantity)`

На странице также отображается детализация времени и стоимости для отмывки и контроля.

# 10. Ручная лакировка (/Handv)

На странице рассчитывается время и стоимость ручной лакировки печатных плат. Предусмотрено три типа лакировки: окунание, кисть и краскопульт. Расчеты производятся в JavaScript-функции `handv_amount()` в шаблоне `Handv.html`.

**Входные параметры (из сессии `/home` и `/second`):**

*   `quantity`: Общее количество ПУ (плат) в партии (`session[\'home_form\'][\'field3\']`).
*   `width_pu`: Ширина одной платы (ПУ), мм (рассчитывается как `session[\'second_form\'][\'width\'] / session[\'second_form\'][\'width_num\']`).
*   `length_pu`: Длина одной платы (ПУ), мм (рассчитывается как `session[\'second_form\'][\'length\'] / session[\'second_form\'][\'length_num\']`).

**Входные параметры (со страницы `/Handv`):**

*   `Handv_active`: Чекбокс \"Выполнять ручную лакировку?\" (поле `Handv`). Если не отмечен, расчеты не производятся.
*   `handv_lak_type`: Тип ручной лакировки (radio-кнопки `Handv_type`):
    *   `1` - Окунание
    *   `2` - Кисть
    *   `3` - Краскопульт
*   Если `handv_lak_type == 2` (Кисть):
    *   `lak_area_width_brush`: Ширина области лакировки кистью, мм (поле `width`).
    *   `lak_area_length_brush`: Длина области лакировки кистью, мм (поле `length`).
*   Если `handv_lak_type == 3` (Краскопульт):
    *   `prep_time_spraygun`: Время на подготовительные работы для краскопульта на ПУ, с (поле `add`).

**Константы из файлов данных:**

*   `data/Handv.csv` (загружается в `df`):
    *   `df[\'Значение\'][0]`: Коэффициент времени для окунания.
    *   `df[\'Значение\'][1]`: Базовое время для окунания, с.
    *   `df[\'Значение\'][2]`: Скорость лакировки кистью, мм/с.
    *   `df[\'Значение\'][3]`: Ширина прохода кистью, мм.
    *   `df[\'Значение\'][4]`: Поправочный коэффициент времени для кисти.
    *   `df[\'Значение\'][5]`: Дополнительное время на работы кистью, с.
    *   `df[\'Значение\'][6]`: Скорость лакировки краскопультом, мм/с.
    *   `df[\'Значение\'][7]`: Ширина прохода краскопультом, мм.
    *   `df[\'Значение\'][8]`: Поправочный коэффициент времени для краскопульта.
    *   `df[\'Значение\'][9]`: Время на контроль 1 ПУ, с.
*   `data/variables.csv` (загружается в `df2`):
    *   `df2[\'Стоимость, руб/ч\'][14]`: Стоимость часа работы для ручной лакировки.
    *   `df2[\'Стоимость, руб/ч\'][21]`: Стоимость часа работы контролера.

**Расчеты (в `Handv.html` - функция `handv_amount()`):**

Если чекбокс `Handv_active` не отмечен, все поля на странице отображают \"-\".

1.  **Время лакировки на 1 ПУ (`t_lak_pc_seconds`):**
    *   Если `handv_lak_type == 1` (Окунание):
        $$ t_{\text{lak\_pc\_seconds}} = \lceil \text{df[\'Значение\'][0]} \times \text{df[\'Значение\'][1]} \rceil $$
    *   Если `handv_lak_type == 2` (Кисть):
        `min_side_lak_brush = min(lak_area_width_brush, lak_area_length_brush)`
        `max_side_lak_brush = max(lak_area_width_brush, lak_area_length_brush)`
        `num_passes_brush = ceil(min_side_lak_brush / df[\'Значение\'][3])`
        $$ t_{\text{lak\_pc\_seconds}} = \lceil (\text{num\_passes\_brush} \times \text{max\_side\_lak\_brush} / \text{df[\'Значение\'][2]}) \times \text{df[\'Значение\'][4]} + \text{df[\'Значение\'][5]} \rceil $$
    *   Если `handv_lak_type == 3` (Краскопульт):
        `min_side_pu = min(width_pu, length_pu)`
        `max_side_pu = max(width_pu, length_pu)`
        `num_passes_spraygun = ceil(min_side_pu / df[\'Значение\'][7])`
        $$ t_{\text{lak\_pc\_seconds}} = \lceil (\text{num\_passes\_spraygun} \times \text{max\_side\_pu} / \text{df[\'Значение\'][6]}) \times \text{df[\'Значение\'][8]} + \text{prep\_time\_spraygun} \rceil $$

2.  **Общее время лакировки партии (`t_lak_all_hours`):**
    $$ t_{\text{lak\_all\_hours}} = \lceil (t_{\text{lak\_pc\_seconds}} \times \text{quantity}) / 3600 \rceil $$

3.  **Стоимость лакировки партии (`cost_lak_all`):**
    $$ \text{cost\_lak\_all} = \lceil t_{\text{lak\_all\_hours}} \times \text{df2[\'Стоимость, руб/ch\'][14]} \rceil $$

4.  **Время контроля партии (`t_control_all_hours`):**
    $$ t_{\text{control\_all\_hours}} = \lceil (\text{quantity} \times \text{df[\'Значение\'][9]}) / 3600 \rceil $$

5.  **Стоимость контроля партии (`cost_control_all`):**
    $$ \text{cost\_control\_all} = \lceil t_{\text{control\_all\_hours}} \times \text{df2[\'Стоимость, руб/ч\'][21]} \rceil $$

6.  **Итоговая стоимость на всю партию (`cost_total_all_handv`):**
    $$ \text{cost\_total\_all\_handv} = \text{cost\_lak\_all} + \text{cost\_control\_all} $$

7.  **Итоговая стоимость на 1 ПУ (`cost_total_pc_handv`):**
    $$ \text{cost\_total\_pc\_handv} = \lceil \text{cost\_total\_all\_handv} / \text{quantity} \rceil $$

На странице отображаются:
*   `time_pc`: `t_lak_pc_seconds` (Время лакировки 1 ПУ)
*   `money_pc`: `ceil(cost_lak_all / quantity)` (Стоимость лакировки 1 ПУ)
*   `time_all`: `t_lak_all_hours` (Время лакировки партии)
*   `money_all`: `cost_lak_all` (Стоимость лакировки партии)
*   `control_time_all`: `t_control_all_hours` (Время контроля партии)
*   `control_money_all`: `cost_control_all` (Стоимость контроля партии)
*   `money_pc_f`: `cost_total_pc_handv` (Итоговая стоимость на 1 ПУ)
*   `money_all_f`: `cost_total_all_handv` (Итоговая стоимость на партию)

# 11. Разделение плат (/separation)

На странице рассчитывается время и стоимость разделения мультизаготовок (МЗ) на отдельные платы (ПУ). Предусмотрено три типа разделения: скрайбирование, разделение по перемычкам и SAR. Предварительные расчеты базового времени на 1 ПУ для каждого типа разделения производятся в Python (`calculations_money.py` - функция `sep_calculations`), а окончательные расчеты общего времени и стоимости – в JavaScript-функции `time_calculation()` в шаблоне `Sep.html`.

**Входные параметры (из сессии `/home` и `/second`):**

*   `quantity`: Общее количество ПУ (плат) в партии (`session[\'home_form\'][\'field3\']`).
*   `width_mz`: Ширина МЗ, мм (`session[\'second_form\'][\'width\']`).
*   `length_mz`: Длина МЗ, мм (`session[\'second_form\'][\'length\']`).
*   `num_pu_length_mz`: Количество плат в длину на МЗ (`session[\'second_form\'][\'length_num\']`).
*   `num_pu_width_mz`: Количество плат в ширину на МЗ (`session[\'second_form\'][\'width_num\']`).

**Промежуточные расчеты в Python (`calculations_money.py` - `sep_calculations()`):**

*   `dist_x_cut_mz = width_mz * (num_pu_length_mz + 1)`: Длина реза по X на МЗ.
*   `dist_y_cut_mz = length_mz * (num_pu_width_mz + 1)`: Длина реза по Y на МЗ.
*   `num_pu_in_mz_py = num_pu_length_mz * num_pu_width_mz`: Количество ПУ в МЗ.
*   `num_mz_in_batch_py = quantity / num_pu_in_mz_py`: Количество МЗ в партии.
*   **Базовое время скрайбирования на 1 ПУ (`t_scrub_pu_py_seconds`):**
    $$ t_{\text{scrub\_pu\_py\_seconds}} = \lceil ((\text{dist\_x\_cut\_mz} + \text{dist\_y\_cut\_mz}) / \text{df_sep[\'Значение\'][0]}) \times \text{df_sep[\'Значение\'][3]} / \text{num\_pu\_in\_mz\_py} \rceil $$
    (где `df_sep[\'Значение\'][0]` - скорость скрайбирования, `df_sep[\'Значение\'][3]` - попр. коэф. времени скрайбирования из `data/Sep.csv`)
*   **Базовое время на перемычки для 1 МЗ (`t_jumpers_mz_py_seconds`):**
    $$ t_{\text{jumpers\_mz\_py\_seconds}} = \text{df_sep[\'Значение\'][1]} \times \text{df_sep[\'Значение\'][4]} $$
    (где `df_sep[\'Значение\'][1]` - время на 1 перемычку, `df_sep[\'Значение\'][4]` - попр. коэф. времени на перемычки из `data/Sep.csv`)
*   **Базовое время SAR на 1 ПУ (`t_sar_pu_py_seconds`):**
    $$ t_{\text{sar\_pu\_py\_seconds}} = \lceil ((\text{dist\_x\_cut\_mz} + \text{dist\_y\_cut\_mz}) / \text{df_sep[\'Значение\'][2]}) \times \text{df_sep[\'Значение\'][5]} / \text{num\_pu\_in\_mz\_py} \rceil $$
    (где `df_sep[\'Значение\'][2]` - скорость SAR, `df_sep[\'Значение\'][5]` - попр. коэф. времени SAR из `data/Sep.csv`)

Результат `[t_scrub_pu_py_seconds, t_jumpers_mz_py_seconds, t_sar_pu_py_seconds, num_mz_in_batch_py, num_pu_in_mz_py]` передается в шаблон JS как массив `time`.

**Входные параметры (со страницы `/separation`):**

*   `Sep_active`: Чекбокс \"Выполнять разделение?\" (поле `Sep`). Если не отмечен, расчеты не производятся.
*   `separation_type`: Тип разделения (radio-кнопки `Sep_type`):
    *   `1` - Скрайбирование
    *   `2` - Перемычки
    *   `3` - SAR
*   Если `separation_type == 1` (Скрайбирование):
    *   `num_jumpers_if_scrubbing`: Количество перемычек при скрайбировании (поле `jumpers2_num`).
*   Если `separation_type == 2` (Перемычки):
    *   `num_jumpers_for_breaking_only`: Количество перемычек для слома (поле `jumpers_num`).

**Константы из файлов данных (используемые в JS):**

*   `data/Sep.csv` (загружается в `df` в Python, значения передаются в JS через `{{df[\'Значение\'][индекс]}}`):
    *   `df[\'Значение\'][3]`: Поправочный коэффициент времени скрайбирования для общего расчета.
    *   `df[\'Значение\'][4]`: Поправочный коэффициент времени на перемычки для общего расчета.
    *   `df[\'Значение\'][5]`: Поправочный коэффициент времени SAR для общего расчета.
*   `data/variables.csv` (загружается в `df2` в Python):
    *   `df2[\'Стоимость, руб/ч\'][15]`: Стоимость часа работы для разделения.

**Расчеты (в `Sep.html` - функция `time_calculation()`):**

1.  **Время разделения на 1 ПУ, используемое в JS (`t_sep_pu_js_calc_seconds`):**
    *   Если `separation_type == 1` (Скрайбирование):
        $$ t_{\text{sep\_pu\_js\_calc\_seconds}} = \lceil \text{time[0]} + (\text{time[1]} \times \text{num\_jumpers\_if\_scrubbing} / \text{time[4]}) \rceil $$
        (где `time[0]` - `t_scrub_pu_py_seconds`, `time[1]` - `t_jumpers_mz_py_seconds`, `time[4]` - `num_pu_in_mz_py`)
    *   Если `separation_type == 2` (Перемычки):
        $$ t_{\text{sep\_pu\_js\_calc\_seconds}} = (\text{time[1]} \times \text{num\_jumpers\_for\_breaking\_only}) / \text{time[4]} $$
    *   Если `separation_type == 3` (SAR):
        $$ t_{\text{sep\_pu\_js\_calc\_seconds}} = \text{time[2]} $$
        (где `time[2]` - `t_sar_pu_py_seconds`)

2.  **Промежуточное время на МЗ (`t_sep_mz_js_calc_seconds`):**
    $$ t_{\text{sep\_mz\_js\_calc\_seconds}} = \lceil t_{\text{sep\_pu\_js\_calc\_seconds}} \times \text{time[4]} \rceil $$

3.  **Общее время разделения партии (`t_sep_all_batch_hours`):**
    (где `time[3]` - `num_mz_in_batch_py`)
    *   Если `separation_type == 1` (Скрайбирование):
        $$ t_{\text{sep\_all\_batch\_hours}} = \lceil (t_{\text{sep\_mz\_js\_calc\_seconds}} \times \text{time[3]} \times \text{df[\'Значение\'][3]}) / 3600 \rceil $$
    *   Если `separation_type == 2` (Перемычки):
        $$ t_{\text{sep\_all\_batch\_hours}} = \lceil (t_{\text{sep\_mz\_js\_calc\_seconds}} \times \text{time[3]} \times \text{df[\'Значение\'][4]}) / 3600 \rceil $$
    *   Если `separation_type == 3` (SAR):
        $$ t_{\text{sep\_all\_batch\_hours}} = \lceil (t_{\text{sep\_mz\_js\_calc\_seconds}} \times \text{time[3]} \times \text{df[\'Значение\'][5]}) / 3600 \rceil $$

4.  **Общая стоимость разделения партии (`cost_sep_all_batch`):**
    $$ \text{cost\_sep\_all\_batch} = \lceil t_{\text{sep\_all\_batch\_hours}} \times \text{df2[\'Стоимость, руб/ч\'][15]} \rceil $$

5.  **Итоговые значения для отображения:**
    *   `time_pc`: `ceil(t_sep_pu_js_calc_seconds)` (Время на 1 ПУ, с)
    *   `time_all`: `t_sep_all_batch_hours` (Время на партию, ч)
    *   `money_all` (и `money_all_f`): `cost_sep_all_batch` (Стоимость на партию, руб)
    *   `money_pc` (и `money_pc_f`): `ceil(cost_sep_all_batch / quantity)` (Стоимость на 1 ПУ, руб)

# 12. Рентген-контроль (/xray)

На странице рассчитывается время и стоимость рентген-контроля.

**Входные параметры:**

*   `Xray_proc`: Процент выборки для контроля (поле `Xray_proc`).
*   `xray_type`: Тип изделия (выбирается radio-кнопками `Xray_type`):
    *   `1` - Серверная плата
    *   `2` - Материнская плата
    *   `3` - Прочее
*   Если выбран тип "Прочее" (`xray_type == 3`):
    *   `xray_comp_time`: Время на проверку одного компонента, с (поле `components_time`).
    *   `xray_num_comps`: Количество компонентов для рентген-контроля (поле `components`).
*   Параметры МЗ (ширина, длина, количество МЗ в мультизаготовке) берутся из сессии (`session['second_form']`).
*   Количество ПУ в партии (`quantity`) берется из сессии (`session['home_form']['field3']`).
*   `{df['Значение'][индекс]}`: Константы из `data/Xray.csv`.
*   `{df2['Стоимость, руб/ч'][индекс]}`: Константы из `data/variables.csv`.

**Расчеты (в `Xray.html` - функция `xray_amount()`):**

Если рентген-контроль не выбран (чекбокс `Xray` не отмечен), то все значения времени и стоимости равны 0 или "-".

Если рентген-контроль выбран:

1.  **Коэффициент вместимости МЗ в кассету рентгена (`coef_mz_in_cassette`):**
    Рассчитывается как максимальное количество МЗ, помещающихся в кассету рентген-аппарата.
    $$ \text{fit_width} = \lfloor \text{df['Значение'][0]} / \text{session['second_form']['width']} \rfloor $$ 
    $$ \text{fit_length} = \lfloor \text{df['Значение'][1]} / \text{session['second_form']['length']} \rfloor $$ 
    $$ \text{coef_mz_in_cassette} = \max( (\text{fit_width} \times \text{fit_length}), 1 ) $$ 
    *(Отображается как `number_Xray_pt`)*

2.  **Количество запусков рентген-контроля (`num_xray_runs`):**
    $$ \text{num_xray_runs} = \lceil (\text{session['second_form']['multi_num']} \times (\text{Xray_proc} / 100)) / \text{coef_mz_in_cassette} \rceil $$ 
    *(Отображается как `number_Xray`)*

3.  **Общее время рентген-контроля партии, секунды (`t_xray_all_seconds`):**

    *   Если тип "Серверная плата" (`xray_type == 1`):
        $$ t_{xray\_all\_seconds} = \text{df['Значение'][3]} \times (\text{Xray_proc} / 100) \times \text{session['second_form']['multi_num']} $$ 

    *   Если тип "Материнская плата" (`xray_type == 2`):
        $$ t_{xray\_all\_seconds} = \text{df['Значение'][2]} \times (\text{Xray_proc} / 100) \times \text{session['second_form']['multi_num']} $$ 

    *   Если тип "Прочее" (`xray_type == 3`):
        $$ t_{xray\_pc\_seconds\_for\_type3} = \text{xray_num_comps} \times \text{xray_comp_time} \times (\text{Xray_proc} / 100) $$ 
        $$ t_{xray\_all\_seconds} = t_{xray\_pc\_seconds\_for\_type3} \times \text{quantity} $$ 

4.  **Время рентген-контроля на 1 ПУ, секунды (`t_xray_pc_seconds`):**

    *   Если тип "Серверная плата" или "Материнская плата":
        $$ t_{xray\_pc\_seconds} = t_{xray\_all\_seconds} / \text{quantity} $$ 

    *   Если тип "Прочее":
        $$ t_{xray\_pc\_seconds} = t_{xray\_pc\_seconds\_for\_type3} $$ 

5.  **Общее время рентген-контроля партии, часы (`t_xray_all_hours`):**
    $$ t_{xray\_all\_hours} = \lceil t_{xray\_all\_seconds} / 3600 \rceil $$ 
    *(В JS переменная `time_all` до округления используется для расчета `money_all`, а затем округляется для отображения)*

6.  **Стоимость рентген-контроля партии (`cost_xray_all`):**
    $$ \text{cost\_xray\_all} = \lceil (t_{xray\_all\_seconds} \times \text{df2['Стоимость, руб/ч'][16]}) / 3600 \rceil $$ 

7.  **Стоимость рентген-контроля на 1 ПУ (`cost_xray_pc`):**
    $$ \text{cost\_xray\_pc} = \lceil \text{cost_xray_all} / \text{quantity} \rceil $$ 

Итоговые значения `cost_xray_all` и `cost_xray_pc` также отображаются как `money_all_f` и `money_pc_f`.

# 13. Упаковка (/pack)

На странице рассчитывается только стоимость упаковки печатных плат. Время на упаковку отдельно не рассчитывается, предполагается, что оно включено в другие операции или пренебрежимо мало. Расчеты производятся в JavaScript-функции `pack_amount()` в шаблоне `Pack.html`.

**Входные параметры (из сессии `/home` и `/second`):**

*   `quantity`: Общее количество ПУ (плат) в партии (`session[\'home_form\'][\'field3\']`).
*   `width_pu_mm`: Ширина одной платы (ПУ), мм (`session[\'second_form\'][\'width_pp\']`).
*   `length_pu_mm`: Длина одной платы (ПУ), мм (`session[\'second_form\'][\'length_pp\']`).

**Входные параметры (со страницы `/pack`):**

*   `Pack_active`: Чекбокс \"Выполнять упаковку?\" (поле `Pack`). Если не отмечен, расчеты не производятся.
*   `box_type_idx`: Индекс выбранного типа короба (от 0 до 7, поле `Pack_type`).
*   `film_type_idx`: Индекс выбранного типа пленки (0 - Пузырчатая, 1 - Экранирующая, поле `Tape_type`).
*   `foam_s1_thick_mm`: Толщина вспененного полиэтилена тип 1, мм (поле `Wisp_1`).
*   `foam_s2_thick_mm`: Толщина вспененного полиэтилена тип 2, мм (поле `Wisp_2`).
*   `foam_s3_thick_mm`: Толщина вспененного полиэтилена тип 3, мм (поле `Wisp_3`).

**Константы из `data/Pack.csv` (загружается в `df`):**

*   **Для коробов (индексы `i` от 0 до 7, соответствуют `box_type_idx`):**
    *   `df[\"Стоимость\"][i]`: Стоимость одного короба i-го типа.
    *   `df[\"Количество\"][i]`: Количество ПУ, помещающихся в короб i-го типа.
*   **Для пленки:**
    *   Индекс `j = 8` (Пузырчатая), если `film_type_idx == 0`.
    *   Индекс `j = 9` (Экранирующая), если `film_type_idx == 1`.
    *   `df[\"Стоимость\"][j]`: Стоимость рулона пленки j-го типа.
    *   `df[\"Длина\"][j]`: Длина рулона пленки j-го типа, мм.
    *   `df[\"Ширина\"][j]`: Ширина рулона пленки j-го типа, мм.
*   **Для вспененного полиэтилена:**
    *   Индекс `k1 = 10` (Тип 1), `k2 = 11` (Тип 2), `k3 = 12` (Тип 3).
    *   `df[\"Стоимость\"][k]`: Стоимость листа/рулона полиэтилена k-го типа.
    *   `df[\"Длина\"][k]`: Условная длина для расчета стоимости за мм полиэтилена k-го типа.

**Расчеты (в `Pack.html` - функция `pack_amount()`):**

1.  **Расчетная площадь 1 ПУ для обертывания пленкой (`pu_film_wrapping_area_mm2`):**
    $$ \text{pu\_film\_wrapping\_area\_mm2} = \lceil \text{width\_pu\_mm} \times \text{length\_pu\_mm} \rceil \times 2.5 $$

2.  **Стоимость коробов на всю партию (`cost_boxes_total`):**
    $$ \text{cost\_boxes\_one} = \text{df[\"Стоимость\"][box\_type\_idx]} $$
    $$ \text{pu\_in\_one\_box} = \text{df[\"Количество\"][box\_type\_idx]} $$
    $$ \text{cost\_boxes\_total} = \lceil (\text{cost\_boxes\_one} \times \text{quantity}) / \text{pu\_in\_one\_box} \rceil $$

3.  **Стоимость пленки на всю партию (`cost_film_total`):**
    Определяется `film_idx_csv` (8 для пузырчатой, 9 для экранирующей) на основе `film_type_idx`.
    $$ \text{film\_roll\_cost} = \text{df[\"Стоимость\"][film\_idx\_csv]} $$
    $$ \text{film\_roll\_area\_mm2} = \text{df[\"Длина\"][film\_idx\_csv]} \times \text{df[\"Ширина\"][film\_idx\_csv]} $$
    $$ \text{cost\_film\_total} = \lceil (\text{pu\_film\_wrapping\_area\_mm2} \times \text{quantity} \times \text{film\_roll\_cost}) / \text{film\_roll\_area\_mm2} \rceil $$

4.  **Стоимость вспененного полиэтилена на всю партию (`cost_foam_total`):**
    $$ \text{cost\_foam\_s1\_per\_mm} = \text{df[\"Стоимость\"][10]} / \text{df[\"Длина\"][10]} $$
    $$ \text{cost\_foam\_s2\_per\_mm} = \text{df[\"Стоимость\"][11]} / \text{df[\"Длина\"][11]} $$
    $$ \text{cost\_foam\_s3\_per\_mm} = \text{df[\"Стоимость\"][12]} / \text{df[\"Длина\"][12]} $$
    $$ \text{cost\_foam\_total} = \lceil ( (\text{foam\_s1\_thick\_mm} \times \text{cost\_foam\_s1\_per\_mm}) + (\text{foam\_s2\_thick\_mm} \times \text{cost\_foam\_s2\_per\_mm}) + (\text{foam\_s3\_thick\_mm} \times \text{cost\_foam\_s3\_per\_mm}) ) \times \text{quantity} \rceil $$

5.  **Общая стоимость упаковки на партию (`cost_all_final`):**
    $$ \text{cost\_all\_final} = \text{cost\_boxes\_total} + \text{cost\_film\_total} + \text{cost\_foam\_total} $$

6.  **Итоговые значения для отображения:**
    *   `money_all`: `ceil(cost_all_final)` (Стоимость на партию, руб)
    *   `money_pc`: `ceil(cost_all_final / quantity)` (Стоимость на 1 ПУ, руб)

# 14. Дополнительные работы (/additional)

На странице рассчитывается время и стоимость до 10-ти (в HTML форме, JS обрабатывает 6 + отдельные поля для ICT) видов дополнительных работ. Для каждой работы указывается описание, выбирается участок (для определения тарифа) и вводится время на одну ПУ. Расчеты производятся в JavaScript (функции `sum()`, `fill_line()`, `fill_line_ict()`) в шаблоне `Add.html`.

**Входные параметры (из сессии `/home`):**

*   `quantity`: Общее количество ПУ (плат) в партии (`session[\'home_form\'][\'field3\']`).

**Входные параметры (для каждой из N строк `i` на странице `/additional`):**

*   `add_work_title_i`: Описание i-й дополнительной работы (поле `title_i`, не влияет на расчет).
*   `add_work_area_idx_i`: Индекс выбранного участка для i-й работы (поле `area_i`). Определяет тариф:
    *   `1` (Тестирование): `hourly_rate_i = df2[\'Стоимость, руб/ч\'][17]`
    *   `2` (Ручной монтаж): `hourly_rate_i = df2[\'Стоимость, руб/ч\'][14]`
    *   `3` (Линия поверхностного монтажа): `hourly_rate_i = df2[\'Стоимость, руб/ч\'][16]`
    *   `4` (Контроль качества): `hourly_rate_i = df2[\'Стоимость, руб/ч\'][21]`
    *   `5` (ICT): `hourly_rate_ict = df2[\'Стоимость, руб/ч\'][18]` (обрабатывается отдельно)
*   `add_work_time_pu_input_seconds_i`: Время на 1 ПУ для i-й работы, с (поле `time_pc_i`).

**Константы из `data/variables.csv` (загружается в `df2` в Python, значения передаются в JS):**

*   `df2[\'Стоимость, руб/ч\'][14]`: Тариф для участка "Ручной монтаж".
*   `df2[\'Стоимость, руб/ч\'][16]`: Тариф для участка "Линия поверхностного монтажа".
*   `df2[\'Стоимость, руб/ч\'][17]`: Тариф для участка "Тестирование".
*   `df2[\'Стоимость, руб/ч\'][18]`: Тариф для участка "ICT".
*   `df2[\'Стоимость, руб/ч\'][21]`: Тариф для участка "Контроль качества".

**Расчеты (в `Add.html` - функции `fill_line()`, `fill_line_ict()` и `sum()`):**

Активация расчетов происходит при отмеченном чекбоксе `Add` (поле `Add`).

**Для каждой обычной дополнительной работы `i` (где участок не ICT):**

1.  **Время на партию (`t_add_work_all_batch_i_hours`):**
    $$ t_{\text{add\_work\_all\_batch\_i\_hours}} = \lceil (\text{add\_work\_time\_pu\_input\_seconds\_i} \times \text{quantity}) / 3600 \rceil $$

2.  **Стоимость на партию (`cost_add_work_all_batch_i`):**
    $$ \text{cost\_add\_work\_all\_batch\_i} = \lceil t_{\text{add\_work\_all\_batch\_i\_hours}} \times \text{hourly\_rate\_i} \rceil $$

3.  **Стоимость на 1 ПУ (`cost_add_work_pu_i`):**
    $$ \text{cost\_add\_work\_pu\_i} = \lceil \text{cost\_add\_work\_all\_batch\_i} / \text{quantity} \rceil $$

**Если выбран участок ICT (обрабатывается `fill_line_ict()`):**

1.  **Время на 1 ПУ (`t_ict_pu_seconds`):** Равно `add_work_time_pu_input_seconds_i` для строки ICT.
2.  **Время на партию (`t_ict_all_batch_hours`):**
    $$ t_{\text{ict\_all\_batch\_hours}} = \lceil (t_{\text{ict\_pu\_seconds}} \times \text{quantity}) / 3600 \rceil $$
3.  **Стоимость на партию (`cost_ict_all_batch`):**
    $$ \text{cost\_ict\_all\_batch} = \lceil t_{\text{ict\_all\_batch\_hours}} \times \text{df2[\'Стоимость, руб/ч\'][18]} \rceil $$
4.  **Стоимость на 1 ПУ (`cost_ict_pu`):**
    $$ \text{cost\_ict\_pu} = \lceil \text{cost\_ict\_all\_batch} / \text{quantity} \rceil $$
    *Эти значения для ICT также отображаются в отдельной секции "Данные по стоимости ICT".*

**Итоговые суммы (отображаются в полях `time_pc`, `time_all`, `money_pc`, `money_all`):**

*   **Общее время на 1 ПУ (`t_total_pu_seconds_display`):**
    Суммируются все `add_work_time_pu_input_seconds_i` (включая время для ICT, если оно есть).
    $$ t_{\text{total\_pu\_seconds\_display}} = \lceil \sum_{i} (\text{add\_work\_time\_pu\_input\_seconds\_i}) \rceil $$

*   **Общее время на партию (`t_total_all_batch_hours_display`):**
    Суммируются `t_add_work_all_batch_i_hours` для всех обычных работ и `t_ict_all_batch_hours` (если есть), затем округляется вверх.
    $$ \text{sum\_seconds} = (\sum_{i \neq ICT} t_{\text{add\_work\_all\_batch\_i\_hours}} \times 3600) + (t_{\text{ict\_all\_batch\_hours}} \times 3600 \text{ if ICT}) $$
    $$ t_{\text{total\_all\_batch\_hours\_display}} = \lceil \text{sum\_seconds} / 3600 \rceil $$

*   **Общая стоимость на партию (`cost_total_all_batch_display`):**
    Суммируются `cost_add_work_all_batch_i` для всех обычных работ и `cost_ict_all_batch` (если есть), затем округляется вверх.
    $$ \text{cost\_total\_all\_batch\_display} = \lceil (\sum_{i \neq ICT} \text{cost\_add\_work\_all\_batch\_i}) + (\text{cost\_ict\_all\_batch} \text{ if ICT}) \rceil $$

*   **Общая стоимость на 1 ПУ (`cost_total_pu_display`):**
    Суммируются `cost_add_work_pu_i` для всех обычных работ и `cost_ict_pu` (если есть), затем округляется вверх.
    $$ \text{cost\_total\_pu\_display} = \lceil (\sum_{i \neq ICT} \text{cost\_add\_work\_pu\_i}) + (\text{cost\_ict\_pu} \text{ if ICT}) \rceil $$

# 15. Дополнительные затраты (/info)

На этой странице вводятся параметры, необходимые для расчета итоговой отпускной цены: процент прибыли и ставка НДС. Непосредственных расчетов времени или промежуточной стоимости здесь не производится. Введенные и отображаемые данные сохраняются в сессии и используются на следующей, финальной странице (`/session_data`) при вызове функции `cm.create_export(session)` для формирования итогового отчета.

**Входные и отображаемые параметры:**

*   **Прибыль (`profit_percentage`):**
    *   Вводится пользователем в поле `Info_proc` (Прибыль в %).
    *   Значение по умолчанию: `30%` (если ранее не было сохранено в сессии).
    *   Сохраняется в `session[\'Info_form\'][\'Info_proc\']`.

*   **НДС (`vat_percentage`):**
    *   Отображается в поле `VAT` (НДС в %, только для чтения на форме без пароля).
    *   Значение загружается из файла `data/Info.csv`, из первого ряда столбца \'Значение\' (`df[\'Значение\'][0]`).
    *   При отправке формы это значение также сохраняется в `session[\'Info_form\'][\'VAT\']`.

**Данные из `data/Info.csv`:**

*   Файл `data/Info.csv` содержит как минимум ставку НДС. Остальные строки (если есть) могут отображаться и редактироваться на странице при наличии прав, но не влияют на автоматические расчеты на этой странице.

**Расчеты:**

На данной странице расчетов **`t_all`** и **`cost_all`** не производится. Эти параметры будут рассчитаны на финальном этапе.

--- 