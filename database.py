import sqlite3
from config import db_table


def prepare_database():
    """
    Функция для создания таблицы.
    """
    try:
        # Установка соединения с базой данных
        connection = sqlite3.connect('sqlite3.db')
        cur = connection.cursor()

        # Создание таблицы students, если она не существует
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            user_name TEXT,
                            subject TEXT,
                            level TEXT,
                            task TEXT,
                            answer TEXT
        );''')
        # cur.execute("""DROP TABLE users""")

        connection.commit()

    except sqlite3.Error as e:
        print("Ошибка при работе с SQLite:", e)
    finally:
        connection.close()


def execute_query(db_file, query, data=None):
    """
    Функция для выполнения запроса к базе данных.
    Принимает имя файла базы данных, SQL-запрос и опциональные данные для вставки.
    """
    try:
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()

        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
            result = cursor.fetchall()
            return result

        connection.commit()

        return

    except sqlite3.Error as e:
        print("Ошибка при выполнении запроса:", e)

    finally:
        connection.close()


def add_user(db_file, user_id, user_name, subject, level, task, answer):
    """
    Функция для добавления нового студента в базу данных.
    """

    #  SQL-запрос для вставки данных о новом пользователе в таблицу users
    query = '''
    INSERT INTO users (user_id, user_name, subject, level, task, answer)
    VALUES (?, ?, ?, ?, ?, ?);
     '''
    data = (user_id, user_name, subject, level, task, answer)

    execute_query(db_file, query, data)
    print("Новый студент успешно добавлен в таблицу.")


def update_user_subject(db_file, subject, user_id):
    """
    Функция для обновления информации в поле subject о существующем пользователе.
    """

    # SQL-запрос для обновления информации о пользователе
    query = '''
    UPDATE users 
    SET subject = ?
    WHERE user_id = ?;
    '''
    data = (subject, user_id)

    execute_query(db_file, query, data)
    print("Информация о студенте успешно обновлена.")


def update_user_level(db_file, level, user_id):
    """
    Функция для обновления уровня объяснения у конкретного пользователя.
    """

    # SQL-запрос для обновления информации о пользователе
    query = '''
    UPDATE users 
    SET level = ?
    WHERE user_id = ?;
    '''
    data = (level, user_id)

    execute_query(db_file, query, data)
    print("Информация о студенте успешно обновлена.")


def update_user_task(db_file, task, user_id):
    """
    Функция для обновления ответа для пользователя.
    """

    # SQL-запрос для обновления информации о пользователе
    query = '''
    UPDATE users 
    SET task = ?
    WHERE user_id = ?;
    '''
    data = (task, user_id)

    execute_query(db_file, query, data)
    print("Информация о студенте успешно обновлена.")


def update_user_answer(db_file, answer, user_id):
    """
    Функция для обновления ответа для пользователя.
    """

    # SQL-запрос для обновления информации о пользователе
    query = '''
    UPDATE users 
    SET answer = ?
    WHERE user_id = ?;
    '''
    data = (answer, user_id)

    execute_query(db_file, query, data)
    print("Информация о студенте успешно обновлена.")


def select_data(db_file, user_id):
    """
    Функция, которая возвращает всю информацию о пользователе.
    """
    query = '''
    SELECT * 
    FROM users
    WHERE user_id = ?;
    '''
    data = (user_id,)
    user = execute_query(db_file, query, data)

    print(user)


def delete_user(db_file, user_id):
    """
    Функция для удаления записи о пользователе из базы данных.
    """

    # SQL-запрос для удаления записи о пользователе
    query = '''
    DELETE FROM users 
    WHERE user_id = ?;
    '''
    data = (user_id,)  # Запятая нужна для кортежа

    execute_query(db_file, query, data)
    print("Запись о студенте успешно удалена.")


def get_user(db_file):
    """
    Функция для получения списка всех студентов, отсортированных по имени.
    """

    #  SQL-запрос для выборки всех студентов из таблицы users
    query = '''
    SELECT * 
    FROM users;
    '''
    users = execute_query(db_file, query)

    for row in users:
        print(row)



#
# add_user(db_table, 12, "a", "2+2", "1", "2+2", "4")
# add_user(db_table, 13, "a", "2+2", "1", "2+2", "4")
# add_user(db_table, 14, "a", "2+2", "1", "2+2", "4")
# add_user(db_table, 15, "a", "2+2", "1", "2+2", "4")
# add_user(db_table, 10, "a", "4+4", "1", "2+2", "8")
# get_user(db_table)
#
# select_data(db_table, 10)
