// SAP Materials Tracking Application

// Конфигурация приложения загружается из файла config.js
// Убедитесь, что он создан из config.example.js и содержит верные данные

// Global variables
let materialsData = { materials: [] };
let chartInstance = null;
let currentSortField = null;
let currentSortDirection = 'asc';
let isLoading = false;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadDataFromGoogleSheets();
});

function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.addEventListener('click', handleRefresh);

    // Table sorting
    setupTableSorting('transitionsTable');
    setupTableSorting('materialsTable');
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
            // Симуляция данных с движениями по разным складам и FIFO логикой
            const rawData = [
                // Материал 3103197 на складе 4749 - поступило 1000, выпущено 300 (FIFO) - 0-10 дней
                ['DOC001', '3103197', '320-00169.B Центр. часть брелка RM-E96', '25.12.2024', '344', '5000', '4749', '11576', 'Мяндин Алексей Юрьевич', '717.18', '3585900.00'],
                ['DOC002', '3103197', '320-00169.B Центр. часть брелка RM-E96', '28.12.2024', '344', '3000', '4749', '11576', 'Мяндин Алексей Юрьевич', '717.18', '2151540.00'],
                ['DOC003', '3103197', '320-00169.B Центр. часть брелка RM-E96', '02.01.2025', '343', '1000', '4749', '11576', 'Мяндин Алексей Юрьевич', '717.18', '717180.00'],
                
                // Тот же материал на другом складе - отдельный учет
                ['DOC004', '3103197', '320-00169.B Центр. часть брелка RM-E96', '30.12.2024', '344', '2000', '4750', '11576', 'Мяндин Алексей Юрьевич', '717.18', '1434360.00'],
                
                // Материал 3100596 - полное освобождение, затем новое поступление - 0-10 дней
                ['DOC005', '3100596', '320-00149.A Стекло ЖКИ брелока A96', '20.12.2024', '344', '20000', '4749', '11576', 'Мяндин Алексей Юрьевич', '256.66', '5133200.00'],
                ['DOC006', '3100596', '320-00149.A Стекло ЖКИ брелока A96', '25.12.2024', '343', '5000', '4749', '11576', 'Мяндин Алексей Юрьевич', '256.66', '1283300.00'],
                ['DOC007', '3100596', '320-00149.A Стекло ЖКИ брелока A96', '05.01.2025', '344', '15000', '4749', '11576', 'Мяндин Алексей Юрьевич', '256.66', '3849900.00'],
                
                // Материал 3105617 - несколько поступлений, частичное списание FIFO - 10-30 дней
                ['DOC008', '3105617', '320-00167.D Стекло ЖКИ RM-E96', '15.12.2024', '344', '5000', '4749', '11576', 'Мяндин Алексей Юрьевич', '2119.00', '10595000.00'],
                ['DOC009', '3105617', '320-00167.D Стекло ЖКИ RM-E96', '20.12.2024', '344', '10000', '4749', '11576', 'Мяндин Алексей Юрьевич', '2119.00', '21190000.00'],
                ['DOC010', '3105617', '320-00167.D Стекло ЖКИ RM-E96', '03.01.2025', '343', '3000', '4749', '11576', 'Мяндин Алексей Юрьевич', '2119.00', '6357000.00'],
                
                // Материал на складе 30-60 дней
                ['DOC011', '3100595', 'Стекло ЖК-брелка A96 (cт.2)', '10.11.2024', '344', '131000', '4749', '11576', 'Мяндин Алексей Юрьевич', '167.76', '21976560.00'],
                
                // Материал на складе 60-90 дней - высокостоимостный
                ['DOC012', '3107699', '911-00036.A RMV-E96 V8510 Si4463 б/к', '01.10.2024', '344', '7200', '4757', '23154', 'Кочетков Евгений Николаевич', '7258.30', '52259760.00'],
                
                // Материал более 90 дней - критическая ситуация
                ['DOC013', '3108001', '320-00120.B Печатная плата брелка A96', '15.08.2024', '344', '4500', '4749', '11576', 'Мяндин Алексей Юрьевич', '1254.00', '5643000.00'],
                
                // Материал с движениями на разных складах - не должны пересекаться
                ['DOC014', '3107779', '320-00356.A Вер.крыш.кор ES96TRX4LIN MIC', '18.12.2024', '344', '100', '4749', '11576', 'Мяндин Алексей Юрьевич', '11.17', '1117.00'],
                ['DOC015', '3107779', '320-00356.A Вер.крыш.кор ES96TRX4LIN MIC', '19.12.2024', '343', '50', '4750', '11576', 'Мяндин Алексей Юрьевич', '11.17', '558.50'], // Не влияет на склад 4749
                
                // Материал с переходом между группами (10-30 дней)
                ['DOC016', '3100594', 'Стекло ЖК-брелка A96 (cт.1)', '20.12.2024', '344', '300', '4749', '11576', 'Мяндин Алексей Юрьевич', '5.43', '1629.00'],
                
                // Дополнительные материалы для демонстрации всех групп
                // 30-60 дней
                ['DOC017', '3109001', 'Резистор 0805 10кОм', '25.10.2024', '344', '1000', '4749', '11576', 'Мяндин Алексей Юрьевич', '0.15', '150.00'],
                
                // 60-90 дней  
                ['DOC018', '3109002', 'Конденсатор керамический 100нФ', '20.09.2024', '344', '500', '4750', '23154', 'Кочетков Евгений Николаевич', '0.25', '125.00'],
                
                // Более 90 дней - очень старый материал
                ['DOC019', '3109003', 'Микросхема обработки сигналов', '10.07.2024', '344', '25', '4757', '23154', 'Кочетков Евгений Николаевич', '850.00', '21250.00']
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

// Parse date string in DD.MM.YYYY format
function parseDate(dateString) {
    const [day, month, year] = dateString.split('.');
    return new Date(year, month - 1, day);
}

// Determine time group based on days in block
function getTimeGroup(days) {
    if (days <= 10) return '0-10 дней';
    if (days <= 30) return '10-30 дней';
    if (days <= 60) return '30-60 дней';
    if (days <= 90) return '60-90 дней';
    return 'Более 90 дней';
}

// Get next group information
function getNextGroupInfo(daysInBlock) {
    if (daysInBlock <= 10) {
        return { nextGroup: '10-30 дней', daysToNext: 11 - daysInBlock };
    } else if (daysInBlock <= 30) {
        return { nextGroup: '30-60 дней', daysToNext: 31 - daysInBlock };
    } else if (daysInBlock <= 60) {
        return { nextGroup: '60-90 дней', daysToNext: 61 - daysInBlock };
    } else if (daysInBlock <= 90) {
        return { nextGroup: 'Более 90 дней', daysToNext: 91 - daysInBlock };
    }
    return { nextGroup: null, daysToNext: null };
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
        '0-10 дней': 0,
        '10-30 дней': 0,
        '30-60 дней': 0,
        '60-90 дней': 0,
        'Более 90 дней': 0
    };

    let totalQuantity = 0;
    let totalCost = 0;
    let totalRecords = 0; // Общее количество записей (материал+склад)
    const uniqueMaterialIds = new Set(); // Уникальные ID материалов

    // Группировка по материалам для диагностики
    const materialGroups = {};
    
    materialsData.materials.forEach((material, index) => {
        // Подсчет по группам
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

    // Обновляем карточки по группам времени
    document.getElementById('stats-0-10').textContent = stats['0-10 дней'];
    document.getElementById('stats-10-30').textContent = stats['10-30 дней'];
    document.getElementById('stats-30-60').textContent = stats['30-60 дней'];
    document.getElementById('stats-60-90').textContent = stats['60-90 дней'];
    document.getElementById('stats-90-plus').textContent = stats['Более 90 дней'];
    
    // Обновляем итоговые показатели
    document.getElementById('stats-unique-items').textContent = formatLargeNumber(uniqueMaterialIds.size); // Уникальные материалы
    document.getElementById('stats-total-qty').textContent = formatLargeNumber(totalQuantity);
    document.getElementById('stats-total-cost').textContent = formatCostForStats(totalCost);
}

function createChart() {
    const ctx = document.getElementById('distributionChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (chartInstance) {
        chartInstance.destroy();
    }

    const stats = {
        '0-10 дней': 0,
        '10-30 дней': 0,
        '30-60 дней': 0,
        '60-90 дней': 0,
        'Более 90 дней': 0
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
                backgroundColor: ['#1FB8CD', '#FFC185', '#B4413C', '#DC2626', '#8B4513'],
                borderColor: ['#1FB8CD', '#FFC185', '#B4413C', '#DC2626', '#8B4513'],
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

function populateTransitionsTable() {
    const tbody = document.getElementById('transitionsTableBody');
    const upcomingTransitions = materialsData.materials
        .filter(material => material.daysToNext !== null && material.daysToNext <= 7)
        .sort((a, b) => a.daysToNext - b.daysToNext);

    tbody.innerHTML = '';

    if (upcomingTransitions.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="9" class="no-data">Нет предстоящих переходов в ближайшие 7 дней</td>';
        tbody.appendChild(row);
        return;
    }

    upcomingTransitions.forEach(material => {
        const row = document.createElement('tr');
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
        tbody.appendChild(row);
    });
}

function populateAllMaterialsTable() {
    const tbody = document.getElementById('materialsTableBody');
    tbody.innerHTML = '';

    materialsData.materials.forEach(material => {
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
        '0-10 дней': 'time-group-badge time-group-0-10',
        '10-30 дней': 'time-group-badge time-group-10-30',
        '30-60 дней': 'time-group-badge time-group-30-60',
        '60-90 дней': 'time-group-badge time-group-60-90',
        'Более 90 дней': 'time-group-badge time-group-90-plus'
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
        ? materialsData.materials.filter(m => m.daysToNext !== null && m.daysToNext <= 7)
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
        row.innerHTML = '<td colspan="9" class="no-data">Нет предстоящих переходов в ближайшие 7 дней</td>';
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