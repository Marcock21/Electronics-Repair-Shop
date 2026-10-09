from database import obtener_conexion


try:
    conexion = obtener_conexion()

    if conexion.is_connected():
        print("====================================")
        print("CONEXIÓN EXITOSA")
        print("Base de datos: taller_reparaciones_2026")
        print("====================================")

    conexion.close()

except Exception as error:
    print("ERROR DE CONEXIÓN")
    print(error)