import os

"""Список вложенных директорий в директории"""
def generate_file_tree(directory):
    file_tree = []

    for folder in os.listdir(directory):
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            file_tree.append(folder)

    return file_tree
"""Список вложенных файлов с расширением .pickle в директории"""
def generate_file_tree2(directory):
    file_tree = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file[-7:] == ".pickle":
                file_tree.append(file[:-7])
    return file_tree

def split_filename(filename):
    file_name, file_extension = os.path.splitext(filename)
    words = file_name.split("_")
    return words