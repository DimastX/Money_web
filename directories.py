import os

# === Функции для работы с директориями и файлами Нужен ли этот файл? ===

# --- Получение списка вложенных директорий --- 
"""Список вложенных директорий в директории"""
def generate_file_tree(directory_path):
    """
    Создает список имен всех непосредственных поддиректорий в указанной директории.

    Args:
        directory_path (str): Путь к директории, которую нужно просканировать.

    Returns:
        list: Список строк с именами поддиректорий.
    """
    file_tree_list = [] # Инициализация списка для хранения имен директорий

    # Перебор всех элементов в указанной директории
    for item_name in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item_name) # Формирование полного пути к элементу
        # Проверка, является ли элемент директорией
        if os.path.isdir(item_path):
            file_tree_list.append(item_name) # Добавление имени директории в список

    return file_tree_list

# --- Получение списка файлов .pickle в директории (без расширения) ---
"""Список вложенных файлов с расширением .pickle в директории"""
def generate_file_tree2(directory_path):
    """
    Создает список имен файлов с расширением .pickle в указанной директории 
    (и ее поддиректориях, т.к. используется os.walk), возвращая имена без расширения.

    Args:
        directory_path (str): Путь к директории для поиска .pickle файлов.

    Returns:
        list: Список строк с именами .pickle файлов (без расширения .pickle).
    """
    pickle_files_list = [] # Инициализация списка для хранения имен файлов

    # Рекурсивный обход директории и ее поддиректорий
    for root_dir, sub_dirs, files_in_dir in os.walk(directory_path):
        for file_name in files_in_dir:
            # Проверка, что файл имеет расширение .pickle
            if file_name.endswith(".pickle"):
                # Добавление имени файла без расширения .pickle в список
                pickle_files_list.append(file_name[:-7]) 
    return pickle_files_list

# --- Разбор имени файла на части по символу подчеркивания ---
# (Не используется в текущей версии приложения, судя по остальному коду)
def split_filename(full_filename):
    """
    Разделяет имя файла (без расширения) на слова по символу подчеркивания '_'.

    Args:
        full_filename (str): Полное имя файла (включая расширение).

    Returns:
        list: Список строк (частей имени файла).
    """
    file_basename, file_extension = os.path.splitext(full_filename) # Отделение имени от расширения
    filename_parts = file_basename.split("_") # Разделение имени файла по символу '_'
    return filename_parts