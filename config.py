# -*- coding: utf-8 -*-
# Файл конфигурации приложения.
# Содержит основные настройки, такие как пути к файлам и другие параметры.

import os

# Определяем абсолютный путь к корневой директории приложения (Money_web).
# __file__ ссылается на текущий файл (config.py).
# os.path.abspath(__file__) получает абсолютный путь к config.py.
# os.path.dirname(...) получает директорию, в которой находится config.py.
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Формируем абсолютный путь к файлу базы данных SQLite.
# База данных 'calculation.db' ожидается в поддиректории 'Calculations' относительно корневой директории приложения.
DB_PATH = os.path.join(APP_DIR, 'Calculations', 'calculation.db') 