import mysql.connector


def get_database_connection():
    return mysql.connector.connect(
        host="10.211.136.187",
        port=3306,
        user="warehouse_user",
        password="Warehouse@123",
        database="warehouse_twin"
    )