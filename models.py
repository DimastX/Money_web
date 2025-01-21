import os
import pickle
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, inspect, text
from werkzeug.datastructures import MultiDict

DATABASE_URL = "sqlite:///Calculations/calculation.db"
engine = create_engine(DATABASE_URL)
metadata = MetaData()

def add_column(table_name, column_name):
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    if column_name not in columns:
        with engine.connect() as conn:
            conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN "{column_name}" TEXT'))
            conn.commit()

def get_next_id(cursor):
    cursor.execute("SELECT MAX(id) FROM calculations")
    max_id = cursor.fetchone()[0]
    return (max_id or 0) + 1

def migrate_data():
    # Drop existing table if it exists
    with engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS calculations'))
        conn.commit()

    # Create new table with proper auto-incrementing ID
    Table('calculations', metadata,
          Column('id', Integer, primary_key=True, autoincrement=True),
          extend_existing=True)

    Table('customers', metadata,
          Column('id', Integer, primary_key=True, autoincrement=True),
          Column('customer', String, unique=True),
          extend_existing=True)

    metadata.create_all(engine)

    db = sqlite3.connect('Calculations/calculation.db')
    cursor = db.cursor()  # Add this line to define cursor

    customers = set()
    base_path = "Calculations"
    current_dir = os.getcwd()
    print(f"Текущая директория: {current_dir}")
    print(f"Ищем путь: {os.path.join(current_dir, base_path)}")

    if os.path.exists(base_path):
        print(f"Директория {base_path} найдена")
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith('.pickle'):
                    file_path = os.path.join(root, file)
                    print(f"Обработка файла: {file_path}")
                    with open(file_path, 'rb') as f:
                        session_data = pickle.load(f)

                    if 'id' in session_data:
                        cursor.execute("SELECT id FROM calculations WHERE id = ?", (session_data['id'],))
                        if cursor.fetchone():
                            session_data['id'] = get_next_id(cursor)

                    # При обработке session_data:
                    if 'home_form' in session_data:
                        customers.add(session_data['home_form']['field1'])
                        home_form_data = dict(session_data['home_form'])  # удаляем home_form из основных данных
                        session_data = {k: dict(v) if isinstance(v, MultiDict) else v for k, v in session_data.items()}  # Преобразуем все MultiDict в словари
                        session_data.update(home_form_data)  # добавляем элементы из home_form напрямую
                    # if 'tables' in session_data:
                        # session_data['tables'] = eval(session_data['tables'])
                        
                    
                    # Добавляем столбцы для всех ключей из session
                    for key in session_data.keys():
                        add_column('calculations', key)
                    
                    # Формируем SQL запрос динамически
                    columns = ', '.join(f'"{key}"' for key in session_data.keys())
                    placeholders = ', '.join(f':{key}' for key in session_data.keys())
                    
                    # Вставляем данные
                    with engine.connect() as conn:
                        conn.execute(
                            text(f'INSERT INTO calculations ({columns}) VALUES ({placeholders})'),
                            {key: str(value) for key, value in session_data.items()}
                        )
                        conn.commit()
        print(f"Найдены следующие customers: {customers}")
        # Сохраняем уникальные значения field1
        with engine.connect() as conn:
            for customer in customers:
                # Проверяем существование записи перед добавлением
                existing = conn.execute(
                    text('SELECT id FROM customers WHERE customer = :customer'),
                    {'customer': customer}
                ).first()
                
                if not existing:
                    print(f"Добавляем customer: {customer}")
                    conn.execute(
                        text('INSERT INTO customers (customer) VALUES (:customer)'),
                        {'customer': customer}
                    )
            conn.commit()
    else:
        print(f"Директория {base_path} не найдена")
    Table('customers', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('customer', String, unique=True),
        extend_existing=True)
    metadata.create_all(engine)

    # Then collect unique field1 values:
    customers = set()
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.pickle'):
                with open(os.path.join(root, file), 'rb') as f:
                    session_data = pickle.load(f)
                    if 'home_form' in session_data and 'field1' in session_data['home_form']:
                        customers.add(session_data['home_form']['field1'])

    # Insert unique customers
    with engine.connect() as conn:
        for customer in customers:
            conn.execute(
                text('INSERT INTO customers (customer) VALUES (:customer)'),
                {'customer': customer}
            )
        conn.commit()
    print("Миграция завершена")

if __name__ == "__main__":
    migrate_data()
