// config.example.js
// 1. Переименуйте этот файл в config.js
// 2. Вставьте ваши данные: API ключ и ID Google Таблицы

const APP_CONFIG = {
    // Получите API ключ в Google Cloud Console -> APIs & Services -> Credentials
    // Он должен начинаться с "AIza..."
    API_KEY: 'YOUR_API_KEY_HERE',

    // ID вашей Google Таблицы (из URL)
    SPREADSHEET_ID: 'YOUR_SPREADSHEET_ID_HERE',
    
    // Диапазон для чтения. Например, 'Имя Листа!A3:K'
    RANGE: 'Export Worksheet!A3:N',
    
    // Диапазон для чтения остатков. Например, 'Имя Листа!A2:J'
    TEMP_DB_RANGE: 'Temp_db!A2:J'
}; 