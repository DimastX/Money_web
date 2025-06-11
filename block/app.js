// SAP Materials Tracking Application

// Конфигурация приложения загружается из файла config.js
// Убедитесь, что он создан из config.example.js и содержит верные данные

// Global variables
let materialsData = { materials: [] };
let chartInstance = null;
let currentSortField = null;
let currentSortDirection = 'asc';
let isLoading = false;

// Filtered data for tables
let filteredTransitions = [];
let filteredMaterials = [];

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadDataFromGoogleSheets();
});

function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.addEventListener('click', handleRefresh);

    // Tab switching
    setupTabSwitching();

    // Table sorting
    setupTableSorting('transitionsTable');
    setupTableSorting('materialsTable');

    // Filters
    setupTableFilters();

    // Export buttons
    setupExportButtons();
}

// Setup tab switching functionality
function setupTabSwitching() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
        });
    });
}

// Setup table filters
function setupTableFilters() {
    // Transitions table filters
    const transitionsFilters = {
        id: document.getElementById('transitions-filter-id'),
        name: document.getElementById('transitions-filter-name'),
        warehouse: document.getElementById('transitions-filter-warehouse'),
        group: document.getElementById('transitions-filter-group')
    };

    // Materials table filters
    const materialsFilters = {
        id: document.getElementById('materials-filter-id'),
        name: document.getElementById('materials-filter-name'),
        warehouse: document.getElementById('materials-filter-warehouse'),
        group: document.getElementById('materials-filter-group')
    };

    // Add event listeners to filters
    Object.values(transitionsFilters).forEach(filter => {
        if (filter) {
            filter.addEventListener('input', () => applyTableFilters('transitions'));
            filter.addEventListener('change', () => applyTableFilters('transitions'));
        }
    });

    Object.values(materialsFilters).forEach(filter => {
        if (filter) {
            filter.addEventListener('input', () => applyTableFilters('materials'));
            filter.addEventListener('change', () => applyTableFilters('materials'));
        }
    });

    // Clear filters buttons
    const clearTransitionsBtn = document.getElementById('clear-transitions-filters');
    const clearMaterialsBtn = document.getElementById('clear-materials-filters');

    if (clearTransitionsBtn) {
        clearTransitionsBtn.addEventListener('click', () => clearTableFilters('transitions'));
    }

    if (clearMaterialsBtn) {
        clearMaterialsBtn.addEventListener('click', () => clearTableFilters('materials'));
    }
}

// Setup export buttons
function setupExportButtons() {
    const exportTransitionsBtn = document.getElementById('export-transitions');
    const exportMaterialsBtn = document.getElementById('export-materials');

    if (exportTransitionsBtn) {
        exportTransitionsBtn.addEventListener('click', () => exportTableData('transitions'));
    }

    if (exportMaterialsBtn) {
        exportMaterialsBtn.addEventListener('click', () => exportTableData('materials'));
    }
}

// Apply filters to table
function applyTableFilters(tableType) {
    const isTransitions = tableType === 'transitions';
    const prefix = isTransitions ? 'transitions' : 'materials';
    
    const filters = {
        id: document.getElementById(`${prefix}-filter-id`)?.value.toLowerCase() || '',
        name: document.getElementById(`${prefix}-filter-name`)?.value.toLowerCase() || '',
        warehouse: document.getElementById(`${prefix}-filter-warehouse`)?.value.toLowerCase() || '',
        group: document.getElementById(`${prefix}-filter-group`)?.value || ''
    };

    const sourceData = isTransitions ? getTransitionsData() : materialsData.materials;
    
    const filteredData = sourceData.filter(item => {
        const matchesId = !filters.id || item.id.toLowerCase().includes(filters.id);
        const matchesName = !filters.name || item.name.toLowerCase().includes(filters.name);
        const matchesWarehouse = !filters.warehouse || item.warehouse.toLowerCase().includes(filters.warehouse);
        const matchesGroup = !filters.group || (isTransitions ? item.nextGroup : item.timeGroup) === filters.group;

        return matchesId && matchesName && matchesWarehouse && matchesGroup;
    });

    if (isTransitions) {
        filteredTransitions = filteredData;
        populateTransitionsTable(filteredData);
    } else {
        filteredMaterials = filteredData;
        populateAllMaterialsTable(filteredData);
    }
}

// Clear table filters
function clearTableFilters(tableType) {
    const prefix = tableType === 'transitions' ? 'transitions' : 'materials';
    
    document.getElementById(`${prefix}-filter-id`).value = '';
    document.getElementById(`${prefix}-filter-name`).value = '';
    document.getElementById(`${prefix}-filter-warehouse`).value = '';
    document.getElementById(`${prefix}-filter-group`).value = '';

    // Reapply filters (now empty)
    applyTableFilters(tableType);
}

// Export table data to XLSX format
function exportTableData(tableType) {
    const isTransitions = tableType === 'transitions';
    const data = isTransitions ? filteredTransitions : filteredMaterials;
    const fileName = isTransitions ? 'предстоящие_переходы' : 'все_материалы';

    if (!data || data.length === 0) {
        showErrorNotification('Нет данных для экспорта');
        return;
    }

    // Проверяем доступность библиотеки XLSX
    if (typeof XLSX === 'undefined') {
        showErrorNotification('Библиотека экспорта недоступна');
        return;
    }

    const headers = isTransitions 
        ? ['ID материала', 'Наименование', 'Количество', 'Склад', 'Номер документа', 'Дней до перехода', 'Следующая группа', 'Стоимость', 'Поместил в блок']
        : ['ID материала', 'Наименование', 'Количество', 'Склад', 'Номер документа', 'Дней в блоке', 'Группа', 'Стоимость', 'Поместил в блок'];

    // Функция для получения числового значения стоимости
    function getCostAsNumber(cost) {
        if (!cost || cost === 0) return 0;
        
        const numericCost = parseFloat(cost);
        return isNaN(numericCost) ? 0 : numericCost;
    }

    // Подготавливаем данные в формате массива массивов
    const wsData = [
        headers, // Заголовки
        ...data.map(item => [
            item.id,
            item.name,
            `${item.quantity} ${item.unit}`,
            item.warehouse,
            item.documentNumber,
            isTransitions ? item.daysToNext : item.daysInBlock,
            isTransitions ? item.nextGroup : item.timeGroup,
            getCostAsNumber(item.totalCost),
            item.responsible
        ])
    ];

    // Создаем рабочую книгу
    const wb = XLSX.utils.book_new();
    
    // Создаем лист из данных
    const ws = XLSX.utils.aoa_to_sheet(wsData);
    
    // Форматируем числовые столбцы
    const costColumnIndex = isTransitions ? 7 : 7; // Столбец "Стоимость" 
    const quantityColumnIndex = 2; // Столбец "Количество"
    const daysColumnIndex = isTransitions ? 5 : 5; // Столбец "Дней до перехода/в блоке"
    
    // Применяем числовое форматирование для столбца стоимости
    for (let row = 1; row < wsData.length; row++) { // Начинаем с 1, пропуская заголовки
        const costCellAddress = XLSX.utils.encode_cell({ r: row, c: costColumnIndex });
        if (ws[costCellAddress]) {
            ws[costCellAddress].t = 'n'; // Устанавливаем тип ячейки как число
            ws[costCellAddress].z = '#,##0'; // Формат числа с разделителями тысяч
        }
        
        // Форматируем столбец дней как число
        const daysCellAddress = XLSX.utils.encode_cell({ r: row, c: daysColumnIndex });
        if (ws[daysCellAddress]) {
            ws[daysCellAddress].t = 'n';
        }
    }
    
    // Настраиваем ширину столбцов
    const colWidths = isTransitions 
        ? [
            { wch: 12 }, // ID материала
            { wch: 40 }, // Наименование  
            { wch: 15 }, // Количество
            { wch: 10 }, // Склад
            { wch: 15 }, // Номер документа
            { wch: 15 }, // Дней до перехода
            { wch: 18 }, // Следующая группа
            { wch: 18 }, // Стоимость
            { wch: 25 }  // Поместил в блок
        ]
        : [
            { wch: 12 }, // ID материала
            { wch: 40 }, // Наименование
            { wch: 15 }, // Количество
            { wch: 10 }, // Склад
            { wch: 15 }, // Номер документа
            { wch: 15 }, // Дней в блоке
            { wch: 18 }, // Группа
            { wch: 18 }, // Стоимость
            { wch: 25 }  // Поместил в блок
        ];
    
    ws['!cols'] = colWidths;

    // Добавляем лист в книгу
    const sheetName = isTransitions ? 'Предстоящие переходы' : 'Все материалы';
    XLSX.utils.book_append_sheet(wb, ws, sheetName);
    
    // Генерируем и сохраняем файл
    const fullFileName = `${fileName}_${new Date().toISOString().split('T')[0]}.xlsx`;
    
    try {
        XLSX.writeFile(wb, fullFileName);
        showNotification(`Таблица "${sheetName}" экспортирована в формате XLSX`);
    } catch (error) {
        console.error('Ошибка при экспорте:', error);
        showErrorNotification('Ошибка при создании файла экспорта');
    }
}

// Load data from Google Sheets using API Key
async function loadDataFromGoogleSheets() {
    if (isLoading) return;
    
    try {
        isLoading = true;
        showLoadingState();

        // Check if API key is configured in config.js
        if (typeof APP_CONFIG === 'undefined' || APP_CONFIG.API_KEY === 'YOUR_API_KEY_HERE') {
            // Use demo data if no API key
            await simulateGoogleSheetsLoad();
            initializeApp();
            showNotification('Используются демо-данные. Создайте config.js из config.example.js и настройте API ключ.');
            return;
        }

        // For large datasets, load data in chunks
        const allData = await loadDataInChunks();
        
        if (allData && allData.length > 0) {
            materialsData.materials = transformGoogleSheetsData(allData);
            initializeApp();
            showNotification(`Данные успешно загружены: ${allData.length} записей`);
        } else {
            throw new Error('Нет данных в таблице');
        }
        
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        
        // Fallback to demo data on error
        await simulateGoogleSheetsLoad();
        initializeApp();
        showErrorNotification(`Ошибка API: ${error.message}. Показаны демо-данные.`);
    } finally {
        isLoading = false;
        hideLoadingState();
    }
}

// Load large dataset in chunks to avoid API limits
async function loadDataInChunks() {
    const CHUNK_SIZE = 1000; // Загружаем по 1000 строк за раз
    const MAX_ROWS = 60000;   // Максимум строк для обработки
    let allData = [];
    let currentRow = 3; // Начинаем с 3 строки (пропускаем заголовки)
    
    const sheetName = APP_CONFIG.RANGE.split('!')[0];
    if (!sheetName) {
        throw new Error('Некорректный формат диапазона в config.js. Пример: "Export Worksheet!A3:K"');
    }
    
    console.log(`Начинаем загрузку данных частями с листа "${sheetName}"...`);
    
    while (currentRow < MAX_ROWS) {
        try {
            const endRow = Math.min(currentRow + CHUNK_SIZE - 1, MAX_ROWS);
            const range = `${sheetName}!A${currentRow}:K${endRow}`;
            
            console.log(`Загружаем строки ${currentRow}-${endRow}...`);
            
            const url = `https://sheets.googleapis.com/v4/spreadsheets/${APP_CONFIG.SPREADSHEET_ID}/values/${range}?key=${APP_CONFIG.API_KEY}`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.error) {
                console.error(`Ошибка загрузки диапазона ${range}:`, data.error.message);
                break;
            }
            
            if (!data.values || data.values.length === 0) {
                console.log(`Нет данных в диапазоне ${range}, завершаем загрузку`);
                break;
            }
            
            // Добавляем данные к общему массиву
            allData = allData.concat(data.values);
            
            // Показываем прогресс
            updateLoadingProgress(allData.length);
            
            currentRow = endRow + 1;
            
            // Небольшая пауза между запросами для избежания rate limiting
            await new Promise(resolve => setTimeout(resolve, 100));
            
        } catch (error) {
            console.error(`Ошибка при загрузке чанка начиная с строки ${currentRow}:`, error);
            break;
        }
    }
    
    console.log(`Загрузка завершена. Всего записей: ${allData.length}`);
    return allData;
}

// Update loading progress indicator
function updateLoadingProgress(loadedRows) {
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.textContent = `Загружено: ${loadedRows} записей...`;
    }
}

// Simulate Google Sheets data for demo
async function simulateGoogleSheetsLoad() {
    return new Promise((resolve) => {
        setTimeout(() => {
            // Симуляция данных с движениями по разным складам и FIFO логикой для новых групп времени
            const rawData = [
                // Материал 3103197 на складе 4749 - поступило недавно, в группе "0-30 дней"
                ['DOC001', '3103197', '320-00169.B Центр. часть брелка RM-E96', '25.12.2024', '344', '5000', '4749', '11576', 'Мяндин Алексей Юрьевич', '717.18', '3585900.00'],
                ['DOC002', '3103197', '320-00169.B Центр. часть брелка RM-E96', '28.12.2024', '344', '3000', '4749', '11576', 'Мяндин Алексей Юрьевич', '717.18', '2151540.00'],
                ['DOC003', '3103197', '320-00169.B Центр. часть брелка RM-E96', '02.01.2025', '343', '1000', '4749', '11576', 'Мяндин Алексей Юрьевич', '717.18', '717180.00'],
                
                // Тот же материал на другом складе - отдельный учет
                ['DOC004', '3103197', '320-00169.B Центр. часть брелка RM-E96', '30.12.2024', '344', '2000', '4750', '11576', 'Мяндин Алексей Юрьевич', '717.18', '1434360.00'],
                
                // Материал 3100596 - группа "0-30 дней"
                ['DOC005', '3100596', '320-00149.A Стекло ЖКИ брелока A96', '20.12.2024', '344', '20000', '4749', '11576', 'Мяндин Алексей Юрьевич', '256.66', '5133200.00'],
                ['DOC006', '3100596', '320-00149.A Стекло ЖКИ брелока A96', '25.12.2024', '343', '5000', '4749', '11576', 'Мяндин Алексей Юрьевич', '256.66', '1283300.00'],
                ['DOC007', '3100596', '320-00149.A Стекло ЖКИ брелока A96', '05.01.2025', '344', '15000', '4749', '11576', 'Мяндин Алексей Юрьевич', '256.66', '3849900.00'],
                
                // Материал 3105617 - группа "0-30 дней" 
                ['DOC008', '3105617', '320-00167.D Стекло ЖКИ RM-E96', '15.12.2024', '344', '5000', '4749', '11576', 'Мяндин Алексей Юрьевич', '2119.00', '10595000.00'],
                ['DOC009', '3105617', '320-00167.D Стекло ЖКИ RM-E96', '20.12.2024', '344', '10000', '4749', '11576', 'Мяндин Алексей Юрьевич', '2119.00', '21190000.00'],
                ['DOC010', '3105617', '320-00167.D Стекло ЖКИ RM-E96', '03.01.2025', '343', '3000', '4749', '11576', 'Мяндин Алексей Юрьевич', '2119.00', '6357000.00'],
                
                // Материал группы "Более 30 дней" - попал в блок в ноябре 2024
                ['DOC011', '3100595', 'Стекло ЖК-брелка A96 (cт.2)', '10.11.2024', '344', '131000', '4749', '11576', 'Мяндин Алексей Юрьевич', '167.76', '21976560.00'],
                
                // Материал группы "Более 30 дней" - попал в блок в октябре 2024
                ['DOC012', '3107699', '911-00036.A RMV-E96 V8510 Si4463 б/к', '01.10.2024', '344', '7200', '4757', '23154', 'Кочетков Евгений Николаевич', '7258.30', '52259760.00'],
                
                // Материал группы "До 2024 года" - попал в блок в декабре 2023
                ['DOC013', '3108001', '320-00120.B Печатная плата брелка A96', '15.12.2023', '344', '4500', '4749', '11576', 'Мяндин Алексей Юрьевич', '1254.00', '5643000.00'],
                
                // Материал группы "До 2024 года" - попал в блок в августе 2023
                ['DOC014', '3109003', 'Микросхема обработки сигналов', '10.08.2023', '344', '25', '4757', '23154', 'Кочетков Евгений Николаевич', '850.00', '21250.00'],
                
                // Материал с движениями на разных складах группы "0-30 дней"
                ['DOC015', '3107779', '320-00356.A Вер.крыш.кор ES96TRX4LIN MIC', '18.12.2024', '344', '100', '4749', '11576', 'Мяндин Алексей Юрьевич', '11.17', '1117.00'],
                ['DOC016', '3107779', '320-00356.A Вер.крыш.кор ES96TRX4LIN MIC', '19.12.2024', '343', '50', '4750', '11576', 'Мяндин Алексей Юрьевич', '11.17', '558.50'], // Не влияет на склад 4749
                
                // Дополнительные материалы для группы "0-30 дней"
                ['DOC017', '3100594', 'Стекло ЖК-брелка A96 (cт.1)', '20.12.2024', '344', '300', '4749', '11576', 'Мяндин Алексей Юрьевич', '5.43', '1629.00'],
                
                // Дополнительные материалы для группы "Более 30 дней"
                ['DOC018', '3109001', 'Резистор 0805 10кОм', '25.10.2024', '344', '1000', '4749', '11576', 'Мяндин Алексей Юрьевич', '0.15', '150.00'],
                ['DOC019', '3109002', 'Конденсатор керамический 100нФ', '20.09.2024', '344', '500', '4750', '23154', 'Кочетков Евгений Николаевич', '0.25', '125.00']
            ];

            materialsData.materials = transformGoogleSheetsData(rawData);
            resolve();
        }, 500);
    });
}

// Transform raw Google Sheets data to application format
function transformGoogleSheetsData(rawData) {
    // Группируем все движения по материалам и складам
    const materialWarehouseMovements = {};
    
    // Сначала собираем все движения
    rawData.forEach((row, index) => {
        const [
            documentNumber, materialCode, materialName, entryDate, 
            statusCode, quantity, warehouse, userId, userName, 
            pricePerUnit, totalCost
        ] = row;

        if (!materialCode || !statusCode || !quantity || !warehouse) return;

        const key = `${materialCode}_${warehouse}`; // Ключ: материал + склад
        if (!materialWarehouseMovements[key]) {
            materialWarehouseMovements[key] = {
                code: materialCode,
                name: materialName,
                warehouse: warehouse,
                movements: [],
                responsible: userName,
                pricePerUnit: parseFloat(pricePerUnit) || 0
            };
        }

        materialWarehouseMovements[key].movements.push({
            date: parseDate(entryDate),
            dateString: entryDate,
            statusCode: statusCode,
            quantity: parseInt(quantity) || 0,
            documentNumber: documentNumber,
            totalCost: parseFloat(totalCost) || 0
        });
    });

    // Обрабатываем каждый материал на каждом складе
    const result = [];
    
    Object.values(materialWarehouseMovements).forEach(materialWarehouse => {
        // Сортируем движения по дате
        materialWarehouse.movements.sort((a, b) => a.date - b.date);
        
        // Создаем стек поступлений (FIFO) - сначала убираем старые
        let incomingStack = []; // [{ date, quantity, cost, documentNumber }]
        let totalCostInBlock = 0;
        let firstBlockDate = null;
        let firstBlockDateString = null;
        
        // Обрабатываем все движения
        materialWarehouse.movements.forEach(movement => {
            if (movement.statusCode === '344') {
                // Материал попал в блок
                if (incomingStack.length === 0) {
                    // Это первое попадание в блок (или после полного освобождения)
                    firstBlockDate = movement.date;
                    firstBlockDateString = movement.dateString;
                }
                
                // Добавляем в стек поступлений
                incomingStack.push({
                    date: movement.date,
                    dateString: movement.dateString,
                    quantity: movement.quantity,
                    cost: movement.totalCost,
                    documentNumber: movement.documentNumber
                });
                
                totalCostInBlock += movement.totalCost;
                
            } else if (movement.statusCode === '343') {
                // Материал выпущен из блока - убираем по FIFO (сначала старые)
                let quantityToRemove = movement.quantity;
                let costToRemove = movement.totalCost;
                
                // Убираем из стека начиная с самых старых
                while (quantityToRemove > 0 && incomingStack.length > 0) {
                    const oldestEntry = incomingStack[0];
                    
                    if (oldestEntry.quantity <= quantityToRemove) {
                        // Убираем всю партию
                        quantityToRemove -= oldestEntry.quantity;
                        totalCostInBlock -= oldestEntry.cost;
                        incomingStack.shift(); // Удаляем из начала массива
                    } else {
                        // Убираем частично
                        const proportionalCost = (oldestEntry.cost / oldestEntry.quantity) * quantityToRemove;
                        oldestEntry.quantity -= quantityToRemove;
                        oldestEntry.cost -= proportionalCost;
                        totalCostInBlock -= proportionalCost;
                        quantityToRemove = 0;
                    }
                }
                
                // Если стек пуст, сбрасываем дату первого попадания
                if (incomingStack.length === 0) {
                    firstBlockDate = null;
                    firstBlockDateString = null;
                    totalCostInBlock = 0;
                } else if (firstBlockDate) {
                    // Обновляем дату первого попадания на дату самой старой оставшейся записи
                    const oldestRemaining = incomingStack[0];
                    firstBlockDate = oldestRemaining.date;
                    firstBlockDateString = oldestRemaining.dateString;
                }
            }
        });

        // Если есть остаток в блоке, добавляем в результат
        if (incomingStack.length > 0 && firstBlockDate) {
            const totalQuantityInBlock = incomingStack.reduce((sum, entry) => sum + entry.quantity, 0);
            
            if (totalQuantityInBlock > 0) {
                const today = new Date();
                const daysInBlock = Math.floor((today - firstBlockDate) / (1000 * 60 * 60 * 24));
                
                // Определяем временную группу
                const timeGroup = getTimeGroup(daysInBlock);
                
                // Определяем следующую группу и дни до перехода
                const { nextGroup, daysToNext } = getNextGroupInfo(daysInBlock);

                result.push({
                    id: materialWarehouse.code,
                    name: materialWarehouse.name,
                    quantity: totalQuantityInBlock,
                    unit: 'шт',
                    entryDate: firstBlockDateString,
                    daysInBlock,
                    timeGroup,
                    status: 'В блоке',
                    daysToNext,
                    nextGroup,
                    responsible: materialWarehouse.responsible,
                    warehouse: materialWarehouse.warehouse,
                    pricePerUnit: materialWarehouse.pricePerUnit,
                    totalCost: totalCostInBlock,
                    statusCode: '344', // Все материалы в результате находятся в блоке
                    documentNumber: incomingStack[0].documentNumber // Номер первого документа в стеке
                });
            }
        }
    });

    return result;
}

// Updated date parsing function
function parseDate(dateString) {
    const [day, month, year] = dateString.split('.');
    return new Date(year, month - 1, day);
}

// Updated time group function for new groups
function getTimeGroup(days) {
    if (days <= 30) {
        return '0-30 дней';
    } else {
        // Для материалов, которые в блоке более 30 дней, нужно определить, 
        // попали ли они в блок в 2024 году или раньше
        const today = new Date();
        const entryDate = new Date(today.getTime() - (days * 24 * 60 * 60 * 1000));
        
        if (entryDate.getFullYear() >= 2024) {
            return 'Более 30 дней';
        } else {
            return 'До 2024 года';
        }
    }
}

// Updated function to get next group info (for transitions table)
function getNextGroupInfo(daysInBlock) {
    const today = new Date();
    const entryDate = new Date(today.getTime() - (daysInBlock * 24 * 60 * 60 * 1000));
    
    // Материалы группы "0-30 дней" переходят в "Более 30 дней"
    if (daysInBlock <= 30) {
        return { daysToNext: 30 - daysInBlock, nextGroup: 'Более 30 дней' };
    }
    
    // Материалы группы "Более 30 дней" могут перейти в "До 2024 года" только если попали в блок в 2024
    if (entryDate.getFullYear() >= 2024) {
        // Считаем дни до конца 2024 года
        const endOf2024 = new Date(2024, 11, 31); // 31 декабря 2024
        const msUntilEndOf2024 = endOf2024.getTime() - entryDate.getTime();
        const daysUntilEndOf2024 = Math.ceil(msUntilEndOf2024 / (1000 * 60 * 60 * 24));
        
        if (daysUntilEndOf2024 > 0) {
            return { daysToNext: daysUntilEndOf2024, nextGroup: 'До 2024 года' };
        }
    }
    
    // Материалы группы "До 2024 года" никуда не переходят
    return { daysToNext: null, nextGroup: null };
}

function initializeApp() {
    updateStatistics();
    createChart();
    populateTransitionsTable();
    populateAllMaterialsTable();
    updateLastUpdateTime();
}

// Format large numbers for statistics cards
function formatLargeNumber(number) {
    if (number >= 1000000) {
        return new Intl.NumberFormat('ru-RU', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
            notation: 'compact',
            compactDisplay: 'short'
        }).format(number);
    }
    
    return new Intl.NumberFormat('ru-RU').format(number);
}

// Format cost for statistics cards with compact notation
function formatCostForStats(cost) {
    if (!cost || cost === 0) return '0 ₽';
    
    if (cost >= 1000000) {
        const formatted = new Intl.NumberFormat('ru-RU', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
            notation: 'compact',
            compactDisplay: 'short'
        }).format(cost);
        return `${formatted} ₽`;
    }
    
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(cost);
}

function updateStatistics() {
    const stats = {
        '0-30 дней': 0,
        'Более 30 дней': 0,
        'До 2024 года': 0
    };

    let totalQuantity = 0;
    let totalCost = 0;
    let totalRecords = 0; // Общее количество записей (материал+склад)
    const uniqueMaterialIds = new Set(); // Уникальные ID материалов

    // Группировка по материалам для диагностики
    const materialGroups = {};
    
    materialsData.materials.forEach((material, index) => {
        // Подсчет по группам
        if (!stats[material.timeGroup]) {
            console.error(`ОШИБКА: Неизвестная группа времени "${material.timeGroup}" у материала ${material.id}`);
            console.log('Доступные ключи stats:', Object.keys(stats));
            console.log('Материал:', material);
            // Принудительно создаем ключ
            stats[material.timeGroup] = 0;
        }
        stats[material.timeGroup]++;
        totalQuantity += material.quantity;
        totalCost += material.totalCost;
        totalRecords++; // Каждая запись - это комбинация материал+склад
        uniqueMaterialIds.add(material.id); // Добавляем уникальный ID материала
        
        // Группировка для диагностики дублей
        if (!materialGroups[material.id]) {
            materialGroups[material.id] = [];
        }
        materialGroups[material.id].push({
            warehouse: material.warehouse,
            quantity: material.quantity,
            timeGroup: material.timeGroup
        });
    });
    
    // Проверка на дубли
    const duplicatedMaterials = Object.keys(materialGroups).filter(materialId => 
        materialGroups[materialId].length > 1
    );
    
    console.log('=== ИТОГОВАЯ СТАТИСТИКА ===');
    console.log('Подсчет по группам:', stats);
    console.log('Сумма по группам:', Object.values(stats).reduce((a, b) => a + b, 0));
    console.log('Общее количество записей (материал+склад):', totalRecords);
    console.log('Уникальных материалов (по ID):', uniqueMaterialIds.size);
    console.log('Общее количество материалов:', totalQuantity);
    console.log('Общая стоимость:', totalCost);
    
    if (duplicatedMaterials.length > 0) {
        console.log('Материалы на нескольких складах:', duplicatedMaterials.length, 'материалов');
        duplicatedMaterials.forEach(materialId => {
            console.log(`- ${materialId}: ${materialGroups[materialId].length} складов`);
        });
    }

    // Обновляем карточки по новым группам времени (с безопасной проверкой)
    const stats030Element = document.getElementById('stats-0-30');
    const stats30PlusElement = document.getElementById('stats-30-plus');
    const statsBefore2024Element = document.getElementById('stats-before-2024');
    const statsUniqueElement = document.getElementById('stats-unique-items');
    const statsTotalQtyElement = document.getElementById('stats-total-qty');
    const statsTotalCostElement = document.getElementById('stats-total-cost');

    if (stats030Element) stats030Element.textContent = stats['0-30 дней'];
    if (stats30PlusElement) stats30PlusElement.textContent = stats['Более 30 дней'];
    if (statsBefore2024Element) statsBefore2024Element.textContent = stats['До 2024 года'];
    
    // Обновляем итоговые показатели
    if (statsUniqueElement) statsUniqueElement.textContent = formatLargeNumber(uniqueMaterialIds.size);
    if (statsTotalQtyElement) statsTotalQtyElement.textContent = formatLargeNumber(totalQuantity);
    if (statsTotalCostElement) statsTotalCostElement.textContent = formatCostForStats(totalCost);
}

function createChart() {
    const ctx = document.getElementById('distributionChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (chartInstance) {
        chartInstance.destroy();
    }

    const stats = {
        '0-30 дней': 0,
        'Более 30 дней': 0,
        'До 2024 года': 0
    };

    materialsData.materials.forEach(material => {
        stats[material.timeGroup]++;
    });

    chartInstance = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(stats),
            datasets: [{
                data: Object.values(stats),
                backgroundColor: ['#1FB8CD', '#FFC185', '#DC2626'],
                borderColor: ['#1FB8CD', '#FFC185', '#DC2626'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: {
                            size: 14
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value} материалов (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Get transitions data for filtering - показываем только материалы с реальными предстоящими переходами
function getTransitionsData() {
    return materialsData.materials
        .filter(material => {
            // Исключаем материалы без предстоящих переходов (daysToNext = null)
            if (material.daysToNext === null) return false;
            
            // Исключаем материалы группы "До 2024 года" - им некуда переходить  
            if (material.timeGroup === 'До 2024 года') return false;
            
            // Показываем только материалы с переходом в ближайшие 30 дней
            return material.daysToNext <= 30 && material.daysToNext >= 0;
        })
        .sort((a, b) => a.daysToNext - b.daysToNext);
}

function populateTransitionsTable(dataToShow = null) {
    const tbody = document.getElementById('transitionsTableBody');
    const upcomingTransitions = dataToShow || getTransitionsData();
    
    // Store for filtering
    if (!dataToShow) {
        filteredTransitions = upcomingTransitions;
    }

    tbody.innerHTML = '';

    if (upcomingTransitions.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="9" class="no-data">Нет предстоящих переходов</td>';
        tbody.appendChild(row);
        return;
    }

    upcomingTransitions.forEach(material => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${material.id}</td>
            <td title="${material.name}">${truncateText(material.name, 40)}</td>
            <td>${material.quantity} ${material.unit}</td>
            <td>${material.warehouse}</td>
            <td>${material.documentNumber}</td>
            <td>${material.daysToNext}</td>
            <td><span class="${getTimeGroupClass(material.nextGroup)}">${material.nextGroup}</span></td>
            <td>${formatCost(material.totalCost)}</td>
            <td title="${material.responsible}">${truncateText(material.responsible, 20)}</td>
        `;
        tbody.appendChild(row);
    });
}

function populateAllMaterialsTable(dataToShow = null) {
    const tbody = document.getElementById('materialsTableBody');
    const materialsToShow = dataToShow || materialsData.materials;
    
    // Store for filtering
    if (!dataToShow) {
        filteredMaterials = materialsToShow;
    }
    
    tbody.innerHTML = '';

    if (materialsToShow.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="9" class="no-data">Нет материалов для отображения</td>';
        tbody.appendChild(row);
        return;
    }

    materialsToShow.forEach(material => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${material.id}</td>
            <td title="${material.name}">${truncateText(material.name, 40)}</td>
            <td>${material.quantity} ${material.unit}</td>
            <td>${material.warehouse}</td>
            <td>${material.documentNumber}</td>
            <td>${material.daysInBlock}</td>
            <td><span class="${getTimeGroupClass(material.timeGroup)}">${material.timeGroup}</span></td>
            <td>${formatCost(material.totalCost)}</td>
            <td title="${material.responsible}">${truncateText(material.responsible, 20)}</td>
        `;
        tbody.appendChild(row);
    });
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

function getTimeGroupClass(timeGroup) {
    const classMap = {
        '0-30 дней': 'time-group-badge time-group-0-30',
        'Более 30 дней': 'time-group-badge time-group-30-plus',
        'До 2024 года': 'time-group-badge time-group-before-2024'
    };
    return classMap[timeGroup] || 'time-group-badge';
}

function setupTableSorting(tableId) {
    const table = document.getElementById(tableId);
    const headers = table.querySelectorAll('th[data-sort]');

    headers.forEach(header => {
        header.classList.add('sortable');
        header.addEventListener('click', () => {
            const field = header.getAttribute('data-sort');
            sortTable(tableId, field);
            updateSortIndicators(tableId, field);
        });
    });
}

function sortTable(tableId, field) {
    const table = document.getElementById(tableId);
    const tbody = table.querySelector('tbody');

    // Determine sort direction
    if (currentSortField === field) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortDirection = 'asc';
        currentSortField = field;
    }

    // Get data source
    const dataSource = tableId === 'transitionsTable' 
        ? getTransitionsData() // Используем ту же логику фильтрации
        : materialsData.materials;

    // Sort data
    const sortedData = [...dataSource].sort((a, b) => {
        let valueA = a[field];
        let valueB = b[field];

        // Handle numeric fields
        if (['daysToNext', 'daysInBlock', 'quantity', 'pricePerUnit', 'totalCost'].includes(field)) {
            valueA = parseFloat(valueA) || 0;
            valueB = parseFloat(valueB) || 0;
        } else {
            valueA = valueA ? valueA.toString().toLowerCase() : '';
            valueB = valueB ? valueB.toString().toLowerCase() : '';
        }

        if (valueA < valueB) return currentSortDirection === 'asc' ? -1 : 1;
        if (valueA > valueB) return currentSortDirection === 'asc' ? 1 : -1;
        return 0;
    });

    // Rebuild table
    tbody.innerHTML = '';
    
    if (sortedData.length === 0 && tableId === 'transitionsTable') {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="9" class="no-data">Нет предстоящих переходов в ближайшие 30 дней</td>';
        tbody.appendChild(row);
        return;
    }

    sortedData.forEach(material => {
        const row = document.createElement('tr');
        if (tableId === 'transitionsTable') {
            row.innerHTML = `
                <td>${material.id}</td>
                <td>${material.name}</td>
                <td>${material.quantity} ${material.unit}</td>
                <td>${material.warehouse}</td>
                <td>${material.documentNumber}</td>
                <td>${material.daysToNext}</td>
                <td><span class="${getTimeGroupClass(material.nextGroup)}">${material.nextGroup}</span></td>
                <td>${formatCost(material.totalCost)}</td>
                <td>${material.responsible}</td>
            `;
        } else {
            row.innerHTML = `
                <td>${material.id}</td>
                <td title="${material.name}">${truncateText(material.name, 40)}</td>
                <td>${material.quantity} ${material.unit}</td>
                <td>${material.warehouse}</td>
                <td>${material.documentNumber}</td>
                <td>${material.daysInBlock}</td>
                <td><span class="${getTimeGroupClass(material.timeGroup)}">${material.timeGroup}</span></td>
                <td>${formatCost(material.totalCost)}</td>
                <td title="${material.responsible}">${truncateText(material.responsible, 20)}</td>
            `;
        }
        tbody.appendChild(row);
    });
}

function updateSortIndicators(tableId, field) {
    const table = document.getElementById(tableId);
    const headers = table.querySelectorAll('th[data-sort]');

    headers.forEach(header => {
        header.classList.remove('sort-asc', 'sort-desc');
        if (header.getAttribute('data-sort') === field) {
            header.classList.add(currentSortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
        }
    });
}

function handleRefresh() {
    loadDataFromGoogleSheets();
}

function showLoadingState() {
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.classList.add('btn--loading');
    refreshBtn.disabled = true;
    refreshBtn.textContent = 'Загрузка...';
}

function hideLoadingState() {
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.classList.remove('btn--loading');
    refreshBtn.disabled = false;
    refreshBtn.textContent = '🔄 Обновить данные';
}

function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('ru-RU', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    document.getElementById('lastUpdateTime').textContent = timeString;
}

function showNotification(message = 'Данные обновлены') {
    const notification = document.getElementById('notification');
    const messageEl = notification.querySelector('.notification__text');
    messageEl.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

function showErrorNotification(message) {
    const notification = document.getElementById('notification');
    const messageEl = notification.querySelector('.notification__text');
    const iconEl = notification.querySelector('.notification__icon');
    
    messageEl.textContent = message;
    iconEl.textContent = '❌';
    notification.classList.add('show', 'notification--error');
    
    setTimeout(() => {
        notification.classList.remove('show', 'notification--error');
        iconEl.textContent = '✅';
    }, 5000);
}

// Handle responsive chart resize
window.addEventListener('resize', function() {
    if (chartInstance) {
        chartInstance.resize();
    }
});

// Format cost with currency
function formatCost(cost) {
    if (!cost || cost === 0) return '0 ₽';
    
    // Для очень больших сумм используем сокращенный формат
    if (cost >= 1000000) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
            notation: 'compact',
            compactDisplay: 'short'
        }).format(cost);
    }
    
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(cost);
}

