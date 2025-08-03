// Данные производственного дашборда
// Глобальные переменные
let filteredData = []; // Инициализируем пустым массивом
let rawData = []; // Переменная для хранения загруженных данных
let operationsChart = null;
let timelineChart = null;
let hoursPieChart = null; // Новая переменная для круговой диаграммы часов
let costPieChart = null;  // Новая переменная для круговой диаграммы стоимости
let currentSort = { field: null, direction: 'asc' };

// Цвета для графиков (расширенная палитра)
const chartColors = [
    '#1FB8CD', '#FFC185', '#B4413C', '#ECEBD5', '#5D878F', 
    '#DB4545', '#D2BA4C', '#964325', '#944454', '#13343B',
    '#6A057F', '#8E44AD', '#2ECC71', '#F1C40F', '#E67E22',
    '#3498DB', '#9B59B6', '#C0392B', '#F39C12', '#27AE60'
];

// Инициализация дашборда
document.addEventListener('DOMContentLoaded', async function() {
    await loadDataFromGoogleSheets(); // Загружаем данные из Google Sheets
    initializeFilters();
    updateDashboard();
    setupEventListeners();
});

// Новая функция для загрузки данных из Google Sheets
async function loadDataFromGoogleSheets() {
    const SPREADSHEET_ID = CONFIG.SPREADSHEET_ID;
    const API_KEY = CONFIG.API_KEY;

    const sheet1_Range = 'Расчёт стоимости изделий!A:H';
    const sheet2_Range = 'Расчёт стоимости изделий THT!A:H';

    const url1 = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}/values/${sheet1_Range}?key=${API_KEY}`;
    const url2 = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}/values/${sheet2_Range}?key=${API_KEY}`;

    try {
        const [response1, response2] = await Promise.all([
            fetch(url1),
            fetch(url2)
        ]);

        if (!response1.ok) throw new Error(`HTTP error for Sheet 1! status: ${response1.status}`);
        if (!response2.ok) throw new Error(`HTTP error for Sheet 2! status: ${response2.status}`);

        const data1 = await response1.json();
        const data2 = await response2.json();

        console.log("--- THT Debug Start ---");
        console.log("Raw response from THT sheet:", data2);


        let smtData = [];
        if (data1.values && data1.values.length >= 2) {
            const headers = data1.values[0];
            const rawGoogleData = data1.values.slice(1);
            smtData = rawGoogleData.map(row => {
                const item = {};
                headers.forEach((header, index) => {
                    const value = row[index];
                    if (!value) return;
                    switch (header) {
                        case 'Дата выполнения':
                            const parts = value.split('.');
                            if (parts.length === 3) {
                                item['Дата выполнения'] = `${parts[2]}-${parts[1]}-${parts[0]}`;
                            } else {
                                item['Дата выполнения'] = value;
                            }
                            break;
                        case 'Участок':
                            item['Участок'] = value.trim();
                            break;
                        case 'Операция':
                            item['Операция'] = value;
                            break;
                        case 'RM':
                            item['RM'] = value;
                            break;
                        case 'Выполненная операция и изделие':
                            item['Выполненная операция и изделие'] = value.trim();
                            break;
                        case 'Часы в целых числах':
                            item['Часы в целых числах'] = parseFloat(String(value).replace(/\s/g, '').replace(',', '.')) || 0;
                            break;
                        case 'Тип операции для контроля себестоимости':
                            item['Тип операции для контроля себестоимости'] = value.trim();
                            break;
                        case 'Стоимость операции в рублях':
                            item['Стоимость операции в рублях'] = parseFloat(String(value).replace(/\s/g, '').replace(',', '.')) || 0;
                            break;
                    }
                });
                return item;
            }).filter(item => item['Дата выполнения']);
        } else {
            console.warn('Нет данных или только заголовки в Google Таблице "Расчёт стоимости изделий".');
        }

        let thtData = [];
        if (data2.values && data2.values.length >= 2) {
            console.log("THT data has enough rows. Processing...");
            const headers = data2.values[0];
            console.log("THT Headers found:", headers);
            const rawGoogleData = data2.values.slice(1);
            thtData = rawGoogleData.map(row => {
                const item = {};
                let lineHours = 0;
                headers.forEach((header, index) => {
                    const value = row[index];
                    if (!value) return;
                    switch (header) {
                        case 'Дата выполнения':
                            const parts = value.split('.');
                            if (parts.length === 3) {
                                item['Дата выполнения'] = `${parts[2]}-${parts[1]}-${parts[0]}`;
                            } else {
                                item['Дата выполнения'] = value;
                            }
                            break;
                        case 'Линия':
                            item['Участок'] = value.trim();
                            break;
                        case 'Изделие':
                            item['Выполненная операция и изделие'] = value.trim();
                            break;
                        case 'Задача RM':
                            item['RM'] = value.trim();
                            break;
                        case 'Время работы линии, ч':
                            const parsedValue = parseFloat(String(value).replace(/\s/g, '').replace(',', '.')) || 0;
                            console.log(`Original THT hours value: "${value}", Parsed as: ${parsedValue}`); // Временная отладка
                            lineHours = parsedValue;
                            break;
                        case 'Ручные операции в смену, сек':
                            // Игнорируем этот столбец по требованию
                            break;
                        case 'Стоимость операции в рублях':
                            item['Стоимость операции в рублях'] = parseFloat(String(value).replace(/\s/g, '').replace(',', '.')) || 0;
                            break;
                    }
                });
                item['Операция'] = 'THT';
                item['Часы в целых числах'] = lineHours; // Данные уже в часах
                if (!item['Участок']) item['Участок'] = 'Не указано';
                if (!item['Выполненная операция и изделие']) item['Выполненная операция и изделие'] = 'Не указано';
                if (!item['Стоимость операции в рублях']) item['Стоимость операции в рублях'] = 0;
                if (!item.hasOwnProperty('RM')) item['RM'] = null;
                item['Тип операции для контроля себестоимости'] = 'THT';
                return item;
            }).filter(item => item['Дата выполнения']);
        } else {
            console.warn('Warning: No data or only headers in THT sheet ("Расчёт стоимости изделий THT").');
            if (data2.values) {
                console.warn(`THT sheet only has ${data2.values.length} row(s).`);
            } else {
                console.warn("The 'values' property is missing in the THT sheet response.");
            }
        }
        console.log("--- THT Debug End ---");

        rawData = [...smtData, ...thtData];
        filteredData = [...rawData];
        // console.log('Пример загруженных данных (первые 10 элементов): ', rawData.slice(0, 10));

    } catch (error) {
        console.error('Ошибка при загрузке данных из Google Таблиц:', error);
        alert('Не удалось загрузить данные дашборда. Пожалуйста, убедитесь, что API-ключ и ID таблицы корректны, а также проверьте консоль браузера для получения дополнительной информации.');
    }
}

// Инициализация фильтров
function initializeFilters() {
    // Заполнение выбора изделий
    const products = [...new Set(rawData.map(item => item['Выполненная операция и изделие']))];
    const productSelect = document.getElementById('productFilter');
    products.forEach(product => {
        const option = document.createElement('option');
        option.value = product;
        option.textContent = product;
        productSelect.appendChild(option);
    });
    
    // Инициализация Select2 для поля продукта
    $(document).ready(function() {
        $('#productFilter').select2({
            placeholder: "Выберите одно или несколько изделий",
            allowClear: true, // Позволяет очищать выбор
            language: {
                noResults: function() {
                    return "Ничего не найдено";
                }
            }
        });
    });

    // Заполнение выбора участков
    const sections = [...new Set(rawData.map(item => item['Участок']))];
    const sectionSelect = document.getElementById('sectionFilter');
    sections.forEach(section => {
        const option = document.createElement('option');
        option.value = section;
        option.textContent = section;
        sectionSelect.appendChild(option);
    });

    // Установка дат по умолчанию
    const dates = rawData.map(item => {
        const dateStr = item['Дата выполнения'];
        const parsedDate = new Date(dateStr);
        return parsedDate;
    }).filter(date => !isNaN(date.getTime())); // Отфильтровываем недействительные даты

    if (dates.length === 0) {
        // Обработка случая, когда действительных дат не найдено
        document.getElementById('dateFrom').value = '';
        document.getElementById('dateTo').value = '';
        console.warn("В данных не найдено действительных дат. Фильтры дат сброшены.");
        return;
    }

    const minDate = new Date(Math.min(...dates));
    const maxDate = new Date(Math.max(...dates));
    
    document.getElementById('dateFrom').value = minDate.toISOString().split('T')[0];
    document.getElementById('dateTo').value = maxDate.toISOString().split('T')[0];
}

// Настройка обработчиков событий
function setupEventListeners() {
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    document.getElementById('resetFilters').addEventListener('click', resetFilters);
    
    // Сортировка таблицы
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', () => sortTable(header.dataset.sort));
    });
}

// Применение фильтров
function applyFilters() {
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    const selectedProducts = $('#productFilter').val(); // Получаем массив выбранных продуктов
    const section = document.getElementById('sectionFilter').value;

    filteredData = rawData.filter(item => {
        const itemDate = new Date(item['Дата выполнения']);
        const fromDate = dateFrom ? new Date(dateFrom) : new Date('1900-01-01');
        
        let toDateFilter;
        if (dateTo) {
            toDateFilter = new Date(dateTo);
            toDateFilter.setDate(toDateFilter.getDate() + 1); // Устанавливаем на начало следующего дня
        } else {
            toDateFilter = new Date('2100-12-31'); // Очень далекая дата в будущем
            toDateFilter.setDate(toDateFilter.getDate() + 1); // Убедимся, что она на начало следующего дня
        }

        return (
            itemDate >= fromDate &&
            itemDate < toDateFilter &&
            (selectedProducts.length === 0 || selectedProducts.includes(item['Выполненная операция и изделие'])) &&
            (section === '' || item['Участок'] === section.trim()) // Обрезаем пробелы при сравнении
        );
    });

    updateDashboard();
}

// Сброс фильтров
function resetFilters() {
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    $('#productFilter').val(null).trigger('change'); // Очистка Select2
    document.getElementById('sectionFilter').value = '';
    
    filteredData = [...rawData];
    updateDashboard();
}

// Обновление KPI карточек
function updateKPIs() {
    const totalHours = filteredData.reduce((sum, item) => sum + item['Часы в целых числах'], 0);
    const totalCost = filteredData.reduce((sum, item) => sum + item['Стоимость операции в рублях'], 0);

    document.getElementById('totalHours').textContent = totalHours.toLocaleString('ru-RU');
    document.getElementById('totalCost').textContent = totalCost.toLocaleString('ru-RU') + ' ₽';
}

// Обновление графика операций
function updateOperationsChart() {
    const ctx = document.getElementById('operationsChart').getContext('2d');
    
    // Группировка данных по операциям
    const operationsData = {};
    filteredData.forEach(item => {
        const operation = item['Операция'];
        if (!operationsData[operation]) {
            operationsData[operation] = { hours: 0, cost: 0 };
        }
        operationsData[operation].hours += item['Часы в целых числах'];
        operationsData[operation].cost += item['Стоимость операции в рублях'];
    });

    const labels = Object.keys(operationsData);
    const hoursData = labels.map(label => operationsData[label].hours);
    const costData = labels.map(label => operationsData[label].cost);

    // Фильтрация нулевых значений для легенды
    const filteredOperations = labels.filter((label, index) => 
        operationsData[label].hours > 0 || operationsData[label].cost > 0
    );
    const filteredHoursData = filteredOperations.map(label => operationsData[label].hours);
    const filteredCostData = filteredOperations.map(label => operationsData[label].cost);

    if (operationsChart) {
        operationsChart.destroy();
    }

    operationsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: filteredOperations,
            datasets: [
                {
                    type: 'line', // Изменяем тип на линию
                    label: 'Часы',
                    data: filteredHoursData,
                    backgroundColor: chartColors[0],
                    borderColor: chartColors[0],
                    borderWidth: 1,
                    yAxisID: 'y',
                    order: 1,
                    fill: false // Отключаем заливку для линии
                },
                {
                    type: 'line',
                    label: 'Стоимость, ₽',
                    data: filteredCostData,
                    backgroundColor: chartColors[1],
                    borderColor: chartColors[1],
                    borderWidth: 2,
                    fill: false, // Отключаем заливку для линии
                    yAxisID: 'y1',
                    order: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            if (context.datasetIndex === 0) {
                                return `Часы: ${context.parsed.y}`;
                            } else {
                                return `Стоимость: ${context.parsed.y.toLocaleString('ru-RU')} ₽`;
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Операции'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Часы'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Стоимость, ₽'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        }
    });
}

// Обновление таймлайн графика
function updateTimelineChart() {
    const ctx = document.getElementById('timelineChart').getContext('2d');
    
    const operationsTotalHours = {};
    let grandTotalHours = 0;

    // Сначала рассчитаем общие часы для каждой операции по всем датам
    filteredData.forEach(item => {
        const operation = item['Операция'];
        const hours = item['Часы в целых числах'];
        operationsTotalHours[operation] = (operationsTotalHours[operation] || 0) + hours;
        grandTotalHours += hours;
    });

    const operationsToGroup = new Set();
    for (const op in operationsTotalHours) {
        if ((operationsTotalHours[op] / grandTotalHours) * 100 < 2) {
            operationsToGroup.add(op);
        }
    }

    // Группировка данных по датам и операциям с учетом 'Прочее'
    const timelineData = {};
    const allUniqueOperations = new Set(); // Для сбора всех уникальных операций, которые НЕ попали в 'Прочее'
    
    filteredData.forEach(item => {
        const date = item['Дата выполнения'];
        let operation = item['Операция'];
        const hours = item['Часы в целых числах'];
        
        if (operationsToGroup.has(operation)) {
            operation = 'Прочее'; // Перенаправляем в категорию Прочее
        } else {
            allUniqueOperations.add(operation);
        }

        if (!timelineData[date]) {
            timelineData[date] = {};
        }
        timelineData[date][operation] = (timelineData[date][operation] || 0) + hours;
    });

    // Убедимся, что 'Прочее' всегда идет последним в легенде, если оно есть
    const finalOperations = Array.from(allUniqueOperations).sort();
    if (operationsToGroup.size > 0) {
        finalOperations.push('Прочее');
    }

    const dates = Object.keys(timelineData).sort();
    const datasets = finalOperations.map((operation, index) => ({
        label: operation,
        data: dates.map(date => timelineData[date][operation] || 0),
        backgroundColor: chartColors[index % chartColors.length],
        borderColor: chartColors[index % chartColors.length],
        borderWidth: 1,
        fill: true
    })).filter(dataset => dataset.data.some(value => value > 0)); // Фильтруем наборы данных с нулевыми значениями

    if (timelineChart) {
        timelineChart.destroy();
    }

    timelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates.map(date => new Date(date).toLocaleDateString('ru-RU')),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} ч`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Дата выполнения'
                    }
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Часы'
                    }
                }
            },
            elements: {
                line: {
                    fill: true
                }
            }
        }
    });
}

// Обновление круговой диаграммы часов
function updateHoursPieChart() {
    const ctx = document.getElementById('hoursPieChart').getContext('2d');

    const operationsHours = {};
    let totalHours = 0;

    filteredData.forEach(item => {
        const operation = item['Операция'];
        const hours = item['Часы в целых числах'];
        operationsHours[operation] = (operationsHours[operation] || 0) + hours;
        totalHours += hours;
    });

    const pieLabels = [];
    const pieData = [];
    let otherHours = 0;

    for (const operation in operationsHours) {
        const percentage = (operationsHours[operation] / totalHours) * 100;
        if (percentage < 2 && totalHours > 0) { // Группируем в 'Прочее' если меньше 2% и есть общие часы
            otherHours += operationsHours[operation];
        } else {
            pieLabels.push(`${operation}: ${operationsHours[operation].toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ч`);
            pieData.push(operationsHours[operation]);
        }
    }

    if (otherHours > 0) { // Добавляем Прочее, только если есть накопленные часы
        pieLabels.push(`Прочее: ${otherHours.toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ч`);
        pieData.push(otherHours);
    }

    if (hoursPieChart) {
        hoursPieChart.destroy();
    }

    hoursPieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: pieLabels,
            datasets: [{
                data: pieData,
                backgroundColor: chartColors.slice(0, pieLabels.length),
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    position: 'right',
                    labels: {
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((sum, current) => sum + current, 0);
                            const percentage = (value / total * 100).toFixed(2);
                            return `${label} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Обновление круговой диаграммы стоимости
function updateCostPieChart() {
    const ctx = document.getElementById('costPieChart').getContext('2d');

    const operationsCost = {};
    let totalCost = 0;

    filteredData.forEach(item => {
        const operation = item['Операция'];
        const cost = item['Стоимость операции в рублях'];
        operationsCost[operation] = (operationsCost[operation] || 0) + cost;
        totalCost += cost;
    });

    const pieLabels = [];
    const pieData = [];
    let otherCost = 0;

    for (const operation in operationsCost) {
        const percentage = (operationsCost[operation] / totalCost) * 100;
        if (percentage < 2 && totalCost > 0) { // Группируем в 'Прочее' если меньше 2% и есть общая стоимость
            otherCost += operationsCost[operation];
        } else {
            pieLabels.push(`${operation}: ${operationsCost[operation].toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ₽`);
            pieData.push(operationsCost[operation]);
        }
    }

    if (otherCost > 0) { // Добавляем Прочее, только если есть накопленная стоимость
        pieLabels.push(`Прочее: ${otherCost.toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ₽`);
        pieData.push(otherCost);
    }

    if (costPieChart) {
        costPieChart.destroy();
    }

    costPieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: pieLabels,
            datasets: [{
                data: pieData,
                backgroundColor: chartColors.slice(0, pieLabels.length),
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    position: 'right',
                    labels: {
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((sum, current) => sum + current, 0);
                            const percentage = (value / total * 100).toFixed(2);
                            return `${label} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Обновление всего дашборда
function updateDashboard() {
    updateKPIs();
    updateOperationsChart();
    updateTimelineChart();
    updateHoursPieChart(); // Вызов новой функции
    updateCostPieChart();  // Вызов новой функции
    updateTable();
}

// Обновление таблицы
function updateTable() {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = '';

    // Агрегация данных по Операции и Участку
    const aggregatedData = {};
    filteredData.forEach(item => {
        const key = `${item['Операция']}-${item['Участок']}`;
        if (!aggregatedData[key]) {
            aggregatedData[key] = {
                'Операция': item['Операция'],
                'Участок': item['Участок'],
                'Часы в целых числах': 0,
                'Стоимость операции в рублях': 0
            };
        }
        aggregatedData[key]['Часы в целых числах'] += item['Часы в целых числах'];
        aggregatedData[key]['Стоимость операции в рублях'] += item['Стоимость операции в рублях'];
    });

    let dataToShow = Object.values(aggregatedData);
    
    // Применение сортировки
    if (currentSort.field) {
        dataToShow.sort((a, b) => {
            let aValue, bValue;
            
            switch (currentSort.field) {
                case 'operation':
                    aValue = a['Операция'];
                    bValue = b['Операция'];
                    break;
                case 'section':
                    aValue = a['Участок'];
                    bValue = b['Участок'];
                    break;
                case 'hours':
                    aValue = a['Часы в целых числах'];
                    bValue = b['Часы в целых числах'];
                    break;
                case 'cost':
                    aValue = a['Стоимость операции в рублях'];
                    bValue = b['Стоимость операции в рублях'];
                    break;
                default:
                    return 0;
            }

            if (typeof aValue === 'string') {
                return currentSort.direction === 'asc' 
                    ? aValue.localeCompare(bValue, 'ru')
                    : bValue.localeCompare(aValue, 'ru');
            } else {
                return currentSort.direction === 'asc' 
                    ? aValue - bValue
                    : bValue - aValue;
            }
        });
    }

    dataToShow.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item['Операция']}</td>
            <td>${item['Участок']}</td>
            <td>${item['Часы в целых числах'].toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            <td>${item['Стоимость операции в рублях'].toLocaleString('ru-RU', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ₽</td>
        `;
        tableBody.appendChild(row);
    });

    // Обновление индикаторов сортировки
    document.querySelectorAll('.sort-indicator').forEach(indicator => {
        indicator.className = 'sort-indicator';
    });
    
    if (currentSort.field) {
        const activeHeader = document.querySelector(`[data-sort="${currentSort.field}"] .sort-indicator`);
        if (activeHeader) {
            activeHeader.classList.add(currentSort.direction);
        }
    }
}

// Сортировка таблицы
function sortTable(field) {
    if (currentSort.field === field) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.field = field;
        currentSort.direction = 'asc';
    }
    
    updateTable();
}