import mysql.connector


def obtener_conexion():
    conexion = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",
        database="taller_reparaciones_2026"
    )

    return conexion