import os
import pickle
import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, inspect, text
from sqlalchemy.exc import OperationalError # Импорт для обработки ошибок SQLAlchemy
from werkzeug.datastructures import MultiDict

# === Настройка подключения к базе данных SQLite ===
# URL для подключения к БД. Файл 'calculation.db' будет создан/использован в директории 'Calculations'.
DATABASE_URL = "sqlite:///Calculations/calculation.db"
# Создание "движка" SQLAlchemy для взаимодействия с БД.
engine = create_engine(DATABASE_URL)
# Объект MetaData для хранения информации о схеме БД.
metadata = MetaData()

# === Вспомогательные функции для работы с БД ===

# --- Динамическое добавление столбца в таблицу, если он отсутствует ---
def add_column(table_name, column_name):
    """
    Проверяет наличие столбца в таблице и добавляет его, если он отсутствует.
    Используется для обеспечения гибкости схемы таблицы 'calculations' при миграции.

    Args:
        table_name (str): Имя таблицы.
        column_name (str): Имя столбца для добавления.
    """
    inspector = inspect(engine) # Инспектор для получения информации о схеме БД.
    try:
        columns = [c['name'] for c in inspector.get_columns(table_name)]
        if column_name not in columns:
            with engine.connect() as conn:
                # Используем text() для выполнения сырого SQL. Имена столбцов в кавычках для безопасности.
                conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN "{column_name}" TEXT'))
                conn.commit() # Подтверждение транзакции
    except OperationalError as e:
        # Обработка случая, если таблица еще не существует (например, при первом запуске миграции)
        print(f"Предупреждение при добавлении столбца '{column_name}' в таблицу '{table_name}': {e}")
        # Таблица будет создана позже функцией metadata.create_all(engine)

# --- Получение следующего доступного ID для таблицы calculations (устарело, т.к. id автоинкрементный) ---
# Примечание: Эта функция может быть не нужна, если 'id' в 'calculations' правильно определен как AUTOINCREMENT PRIMARY KEY.
# def get_next_id(cursor):
#     cursor.execute("SELECT MAX(id) FROM calculations")
#     max_id = cursor.fetchone()[0]
#     return (max_id or 0) + 1

# === Основная функция миграции данных из .pickle файлов в SQLite ===
def migrate_data():
    """
    Выполняет миграцию данных из старых файлов .pickle в таблицы SQLite 'calculations' и 'customers'.
    - Удаляет и пересоздает таблицу 'calculations' для чистого старта.
    - Создает таблицу 'customers', если она не существует.
    - Рекурсивно обходит директорию 'Calculations', ищет .pickle файлы.
    - Для каждого .pickle файла:
        - Загружает данные сессии.
        - Динамически добавляет необходимые столбцы в таблицу 'calculations'.
        - Вставляет данные из сессии в таблицу 'calculations'.
        - Собирает уникальные имена заказчиков ('field1' из 'home_form').
    - Вставляет уникальные имена заказчиков в таблицу 'customers'.
    """
    print("Запуск миграции данных...")
    
    # --- Определение и создание структуры таблиц --- 
    # Удаление существующей таблицы 'calculations' для предотвращения дубликатов и конфликтов при повторной миграции.
    # В реальном приложении здесь нужна более аккуратная стратегия (например, проверка или бэкап).
    try:
        with engine.connect() as conn:
            conn.execute(text('DROP TABLE IF EXISTS calculations'))
            conn.commit()
        print("Таблица 'calculations' успешно удалена (если существовала).")
    except Exception as e:
        print(f"Ошибка при удалении таблицы 'calculations': {e}")

    # Определение таблицы 'calculations' с автоинкрементным первичным ключом 'id'.
    # extend_existing=True позволяет переопределить таблицу, если она уже объявлена в metadata.create_all(engine)
    Table('calculations', metadata,
          Column('id', Integer, primary_key=True, autoincrement=True),
          extend_existing=True)
    print("Схема таблицы 'calculations' определена.")

    # Определение таблицы 'customers' для хранения уникальных заказчиков.
    Table('customers', metadata,
          Column('id', Integer, primary_key=True, autoincrement=True),
          Column('customer', String, unique=True), # Имя заказчика должно быть уникальным.
          extend_existing=True)
    print("Схема таблицы 'customers' определена.")

    # Создание всех определенных таблиц в БД, если они еще не существуют.
    metadata.create_all(engine)
    print("Таблицы успешно созданы/обновлены в базе данных.")

    # Используем sqlite3 для некоторых операций, где SQLAlchemy может быть избыточен или для совместимости со старым кодом
    # (хотя предпочтительнее использовать SQLAlchemy engine для всех взаимодействий).
    db_sqlite_conn = sqlite3.connect('Calculations/calculation.db')
    cursor_sqlite = db_sqlite_conn.cursor()

    customers_set = set() # Множество для хранения уникальных имен заказчиков.
    base_calculations_path = "Calculations" # Путь к директории с .pickle файлами.
    # current_working_dir = os.getcwd()
    # print(f"Текущая рабочая директория: {current_working_dir}")
    # print(f"Поиск файлов в: {os.path.join(current_working_dir, base_calculations_path)}")

    if not os.path.exists(base_calculations_path):
        print(f"ОШИБКА: Директория '{base_calculations_path}' не найдена. Миграция не может быть выполнена.")
        return
    
    print(f"Начат обход директории '{base_calculations_path}' для поиска .pickle файлов...")
    # --- Итерация по .pickle файлам и перенос данных --- 
    for root_dir, _, files_in_dir in os.walk(base_calculations_path):
        for filename in files_in_dir:
            if filename.endswith('.pickle'):
                pickle_file_path = os.path.join(root_dir, filename)
                # print(f"Обработка файла: {pickle_file_path}")
                try:
                    with open(pickle_file_path, 'rb') as f_pickle:
                        session_data_from_pickle = pickle.load(f_pickle)
                except Exception as e:
                    print(f"Ошибка при чтении/десериализации файла {pickle_file_path}: {e}. Файл пропущен.")
                    continue
                
                # Обработка данных 'home_form' и извлечение имени заказчика.
                if 'home_form' in session_data_from_pickle and isinstance(session_data_from_pickle['home_form'], (dict, MultiDict)):
                    if 'field1' in session_data_from_pickle['home_form']:
                        customers_set.add(session_data_from_pickle['home_form']['field1'])
                    
                    # Преобразование MultiDict из home_form в обычный dict и "поднятие" его ключей на верхний уровень session_data.
                    home_form_content = dict(session_data_from_pickle['home_form'])
                    session_data_processed = {k: dict(v) if isinstance(v, MultiDict) else v for k, v in session_data_from_pickle.items() if k != 'home_form'}
                    session_data_processed.update(home_form_content)
                else:
                    session_data_processed = {k: dict(v) if isinstance(v, MultiDict) else v for k, v in session_data_from_pickle.items()}
                
                # Удаляем старый 'id' из pickle, так как в БД он автоинкрементный
                if 'id' in session_data_processed:
                    del session_data_processed['id']

                # Динамическое добавление столбцов в таблицу 'calculations' для всех ключей из текущего pickle.
                for key in session_data_processed.keys():
                    add_column('calculations', key)
                
                # Формирование SQL запроса для вставки данных.
                # Ключи оборачиваются в двойные кавычки для SQL, плейсхолдеры именуются по ключам.
                insert_columns_str = ', '.join(f'"{key}"' for key in session_data_processed.keys())
                insert_placeholders_str = ', '.join(f':{key}' for key in session_data_processed.keys())
                
                # Преобразование всех значений в строки для универсальной вставки.
                data_to_insert = {key: str(value) for key, value in session_data_processed.items()}
                
                # Вставка данных в таблицу 'calculations' через SQLAlchemy engine.
                try:
                    with engine.connect() as conn:
                        conn.execute(
                            text(f'INSERT INTO calculations ({insert_columns_str}) VALUES ({insert_placeholders_str})'),
                            data_to_insert
                        )
                        conn.commit()
                    # print(f"Данные из {filename} успешно вставлены.")
                except Exception as e:
                    print(f"Ошибка при вставке данных из {filename} в таблицу 'calculations': {e}")

    print(f"Обход .pickle файлов завершен. Найдено уникальных заказчиков: {len(customers_set)}")

    # --- Сохранение уникальных имен заказчиков в таблицу 'customers' --- 
    if customers_set:
        print("Добавление уникальных заказчиков в таблицу 'customers'...")
        try:
            with engine.connect() as conn:
                for customer_name in customers_set:
                    if customer_name: # Проверка, что имя заказчика не пустое
                        # Проверка, существует ли уже такой заказчик, чтобы избежать дубликатов.
                        existing_customer = conn.execute(
                            text('SELECT id FROM customers WHERE customer = :customer_name_param'),
                            {'customer_name_param': customer_name}
                        ).first()
                        
                        if not existing_customer:
                            conn.execute(
                                text('INSERT INTO customers (customer) VALUES (:customer_name_param)'),
                                {'customer_name_param': customer_name}
                            )
                conn.commit()
            print("Уникальные заказчики успешно добавлены в таблицу 'customers'.")
        except Exception as e:
            print(f"Ошибка при добавлении заказчиков в таблицу 'customers': {e}")
    else:
        print("Уникальные заказчики для добавления не найдены.")

    # Повторное определение и создание таблицы customers здесь избыточно, т.к. это было сделано выше.
    # Table('customers', metadata, ...)
    # metadata.create_all(engine)

    # Секция кода ниже дублирует логику сбора и вставки заказчиков, которая уже была выполнена.
    # Она может быть удалена для избежания повторных операций или ошибок.
    # print("Повторный сбор и вставка заказчиков (дублирующая логика)...")
    # customers_set_duplicate_logic = set()
    # if os.path.exists(base_calculations_path): 
    #     for root_dir, _, files_in_dir in os.walk(base_calculations_path):
    #         for filename in files_in_dir:
    #             if filename.endswith('.pickle'):
    #                 try:
    #                     with open(os.path.join(root_dir, filename), 'rb') as f_pickle:
    #                         session_data_from_pickle = pickle.load(f_pickle)
    #                         if 'home_form' in session_data_from_pickle and \ 
    #                            isinstance(session_data_from_pickle['home_form'], (dict, MultiDict)) and \ 
    #                            'field1' in session_data_from_pickle['home_form']:
    #                             customers_set_duplicate_logic.add(session_data_from_pickle['home_form']['field1'])
    #                 except Exception: # Игнорируем ошибки чтения на этом этапе, т.к. основная миграция прошла
    #                     pass
    # if customers_set_duplicate_logic:
    #     try:
    #         with engine.connect() as conn:
    #             for customer_name in customers_set_duplicate_logic:
    #                 if customer_name: 
    #                     # Эта вставка также должна проверять на существование, чтобы избежать ошибок уникальности
    #                     existing_customer = conn.execute(text('SELECT id FROM customers WHERE customer = :cnp'), {'cnp': customer_name}).first()
    #                     if not existing_customer:
    #                         conn.execute(text('INSERT INTO customers (customer) VALUES (:cnp)'), {'cnp': customer_name})
    #             conn.commit()
    #         print("Дублирующая логика вставки заказчиков завершена.")
    #     except Exception as e:
    #         print(f"Ошибка в дублирующей логике вставки заказчиков: {e}")

    print("Миграция данных завершена.")

# --- Точка входа для запуска миграции --- 
if __name__ == "__main__":
    # Эта проверка позволяет запускать migrate_data() только при прямом выполнении скрипта.
    migrate_data()
