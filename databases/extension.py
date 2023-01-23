import sqlite3
from sqlite3 import Error

DB_PATH = 'cepu_qr.db'


# Подключение к БД
def create_connection(path: str):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Успешное подключение к SQLite")
    except Error as e:
        print(f"Ошибка при подключении: '{e}'")
    return connection


# Запрос на выборку
def execute_read_query(query: str) -> list:
    try:
        connection = create_connection(DB_PATH)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute(query)
        query = cursor.fetchall()
        list_query = []
        for i in query:
            list_query.append({k: i[k] for k in i.keys()})
        connection.close()
        return list_query
    except Error as e:
        print(f"Ошибка запроса: '{e}'")


# Запрос на добавление, изменение, удаление
def execute_query(query: str) -> int:
    try:
        connection = create_connection(DB_PATH)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        last_rowid_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return last_rowid_id
    except Error as e:
        print(f"Ошибка запроса: '{e}'")
