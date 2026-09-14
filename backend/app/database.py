import mysql.connector


def get_database_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="6618",
        database="warehouse_twin"
    )