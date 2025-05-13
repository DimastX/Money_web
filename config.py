import os

# Определяем абсолютный путь к директории, где находится этот файл (config.py)
# Это будет директория Money_web
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Формируем абсолютный путь к файлу базы данных
DB_PATH = os.path.join(APP_DIR, 'Calculations', 'calculation.db') 