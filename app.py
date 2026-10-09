from flask import Flask, render_template, request, redirect, url_for, session
from database import obtener_conexion


app = Flask(__name__)

# Clave utilizada para las sesiones de Flask
app.secret_key = "clave-secreta-taller-2026"


@app.route("/")
def inicio():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        contrasena = request.form["contrasena"]

        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        consulta = """
            SELECT *
            FROM usuarios
            WHERE usuario = %s
            AND contrasena = %s
            AND activo = 1
        """

        cursor.execute(consulta, (usuario, contrasena))

        usuario_encontrado = cursor.fetchone()

        cursor.close()
        conexion.close()

        if usuario_encontrado:

            session["usuario_id"] = usuario_encontrado["idUsuario"]
            session["usuario"] = usuario_encontrado["usuario"]
            session["nombre"] = usuario_encontrado["nombre"]
            session["rol"] = usuario_encontrado["idRol"]

            return redirect(url_for("panel"))

        else:
            return render_template(
                "login.html",
                error="Usuario o contraseña incorrectos."
            )

    return render_template("login.html")


@app.route("/clientes")
def clientes():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    busqueda = request.args.get("buscar", "").strip()

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    if busqueda:

        consulta = """
            SELECT
                idCliente,
                nombre,
                apellido,
                telefono,
                email,
                direccion,
                fechaRegistro
            FROM clientes
            WHERE nombre LIKE %s
               OR apellido LIKE %s
               OR telefono LIKE %s
               OR email LIKE %s
            ORDER BY idCliente DESC
        """

        termino = f"%{busqueda}%"

        cursor.execute(
            consulta,
            (termino, termino, termino, termino)
        )

    else:

        cursor.execute("""
            SELECT
                idCliente,
                nombre,
                apellido,
                telefono,
                email,
                direccion,
                fechaRegistro
            FROM clientes
            ORDER BY idCliente DESC
        """)

    clientes = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "clientes.html",
        clientes=clientes,
        busqueda=busqueda
    )
@app.route("/clientes/nuevo", methods=["GET", "POST"])
def nuevo_cliente():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        nombre = request.form["nombre"].strip()
        apellido = request.form["apellido"].strip()
        telefono = request.form["telefono"].strip()
        email = request.form["email"].strip()
        direccion = request.form["direccion"].strip()

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO clientes
            (nombre, apellido, telefono, email, direccion)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            nombre,
            apellido,
            telefono,
            email,
            direccion
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(url_for("clientes"))

    return render_template("nuevo_cliente.html")

@app.route("/clientes/<int:idCliente>")
def detalle_cliente(idCliente):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Buscar cliente
    cursor.execute("""
        SELECT
            idCliente,
            nombre,
            apellido,
            telefono,
            email,
            direccion,
            fechaRegistro
        FROM clientes
        WHERE idCliente = %s
    """, (idCliente,))

    cliente = cursor.fetchone()

    if not cliente:
        cursor.close()
        conexion.close()
        return "Cliente no encontrado", 404

    # Buscar equipos del cliente
    cursor.execute("""
        SELECT
            idEquipo,
            tipo,
            marca,
            modelo,
            numeroSerie,
            fechaRegistro
        FROM equipos
        WHERE idCliente = %s
        ORDER BY idEquipo DESC
    """, (idCliente,))

    equipos = cursor.fetchall()

    # Buscar órdenes de reparación de los equipos del cliente
    cursor.execute("""
        SELECT
            o.idOrden,
            o.numeroOrden,
            o.fechaIngreso,
            o.fechaFinalizacion,
            o.prioridad,
            e.tipo,
            e.marca,
            e.modelo,
            er.nombre AS estado
        FROM ordenes_reparacion o
        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo
        INNER JOIN estados_reparacion er
            ON o.idEstado = er.idEstado
        WHERE e.idCliente = %s
        ORDER BY o.idOrden DESC
    """, (idCliente,))

    reparaciones = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "detalle_cliente.html",
        cliente=cliente,
        equipos=equipos,
        reparaciones=reparaciones
    )

@app.route("/clientes/editar/<int:idCliente>", methods=["GET", "POST"])
def editar_cliente(idCliente):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Obtener los datos actuales del cliente
    cursor.execute("""
        SELECT *
        FROM clientes
        WHERE idCliente = %s
    """, (idCliente,))

    cliente = cursor.fetchone()

    cursor.close()
    conexion.close()

    if not cliente:
        return "Cliente no encontrado", 404

    # Si se envió el formulario
    if request.method == "POST":

        nombre = request.form["nombre"].strip()
        apellido = request.form["apellido"].strip()
        telefono = request.form["telefono"].strip()
        email = request.form["email"].strip()
        direccion = request.form["direccion"].strip()

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE clientes
            SET nombre = %s,
                apellido = %s,
                telefono = %s,
                email = %s,
                direccion = %s
            WHERE idCliente = %s
        """, (
            nombre,
            apellido,
            telefono,
            email,
            direccion,
            idCliente
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(url_for("clientes"))

    return render_template(
        "editar_cliente.html",
        cliente=cliente
    )

@app.route("/equipos")
def equipos():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            e.idEquipo,
            e.tipo,
            e.marca,
            e.modelo,
            e.numeroSerie,
            e.fallaInformada,
            e.observaciones,
            e.fechaRegistro,
            c.idCliente,
            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente
        FROM equipos e
        INNER JOIN clientes c
            ON e.idCliente = c.idCliente
        ORDER BY e.idEquipo DESC
    """)

    equipos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "equipos.html",
        equipos=equipos
    )

@app.route("/equipos/nuevo", methods=["GET", "POST"])
def nuevo_equipo():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        idCliente = request.form["idCliente"]
        tipo = request.form["tipo"].strip()
        marca = request.form["marca"].strip()
        modelo = request.form["modelo"].strip()
        numeroSerie = request.form["numeroSerie"].strip()
        fallaInformada = request.form["fallaInformada"].strip()
        observaciones = request.form["observaciones"].strip()

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO equipos
            (
                idCliente,
                tipo,
                marca,
                modelo,
                numeroSerie,
                fallaInformada,
                observaciones
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            idCliente,
            tipo,
            marca,
            modelo,
            numeroSerie,
            fallaInformada,
            observaciones
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(url_for("equipos"))

    # Obtener clientes para el selector
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            idCliente,
            nombre,
            apellido
        FROM clientes
        ORDER BY apellido, nombre
    """)

    clientes = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "nuevo_equipo.html",
        clientes=clientes
    )

@app.route("/equipos/<int:idEquipo>")
def detalle_equipo(idEquipo):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Datos del equipo y su cliente
    cursor.execute("""
        SELECT
            e.idEquipo,
            e.tipo,
            e.marca,
            e.modelo,
            e.numeroSerie,
            e.fallaInformada,
            e.observaciones,
            e.fechaRegistro,
            c.idCliente,
            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente
        FROM equipos e
        INNER JOIN clientes c
            ON e.idCliente = c.idCliente
        WHERE e.idEquipo = %s
    """, (idEquipo,))

    equipo = cursor.fetchone()

    if not equipo:
        cursor.close()
        conexion.close()
        return "Equipo no encontrado", 404

    # Historial de órdenes del equipo
    cursor.execute("""
        SELECT
            o.idOrden,
            o.numeroOrden,
            o.fechaIngreso,
            o.fechaFinalizacion,
            o.prioridad,
            e2.nombre AS estado,
            u.nombre AS nombreTecnico,
            u.apellido AS apellidoTecnico
        FROM ordenes_reparacion o
        INNER JOIN estados_reparacion e2
            ON o.idEstado = e2.idEstado
        LEFT JOIN usuarios u
            ON o.idTecnico = u.idUsuario
        WHERE o.idEquipo = %s
        ORDER BY o.idOrden DESC
    """, (idEquipo,))

    reparaciones = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "detalle_equipo.html",
        equipo=equipo,
        reparaciones=reparaciones
    )

@app.route("/reparaciones/nueva/<int:idEquipo>", methods=["GET", "POST"])
def nueva_reparacion(idEquipo):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Obtener datos del equipo y del cliente
    cursor.execute("""
        SELECT
            e.idEquipo,
            e.tipo,
            e.marca,
            e.modelo,
            e.numeroSerie,
            e.fallaInformada,
            e.observaciones,
            c.idCliente,
            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente
        FROM equipos e
        INNER JOIN clientes c
            ON e.idCliente = c.idCliente
        WHERE e.idEquipo = %s
    """, (idEquipo,))

    equipo = cursor.fetchone()

    if not equipo:
        cursor.close()
        conexion.close()
        return "Equipo no encontrado", 404

    # Obtener técnicos activos
    cursor.execute("""
    SELECT
        idUsuario,
        nombre,
        apellido
    FROM usuarios
    WHERE idRol = 3
    AND activo = 1
    ORDER BY apellido, nombre
""")

    tecnicos = cursor.fetchall()

    # Obtener estados de reparación
    cursor.execute("""
        SELECT
            idEstado,
            nombre
        FROM estados_reparacion
        ORDER BY idEstado
    """)

    estados = cursor.fetchall()

    # Guardar nueva orden
    if request.method == "POST":

        idTecnico = request.form["idTecnico"]
        idEstado = request.form["idEstado"]
        prioridad = request.form["prioridad"]
        problemaInformado = request.form["problemaInformado"].strip()
        observaciones = request.form["observaciones"].strip()

        cursor.execute("""
            INSERT INTO ordenes_reparacion
            (
                idEquipo,
                idTecnico,
                idEstado,
                prioridad,
                problemaInformado,
                observaciones
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            idEquipo,
            idTecnico,
            idEstado,
            prioridad,
            problemaInformado,
            observaciones
        ))

        idOrden = cursor.lastrowid

        # Generar número de orden
        numeroOrden = f"ORD-{idOrden:06d}"

        cursor.execute("""
            UPDATE ordenes_reparacion
            SET numeroOrden = %s
            WHERE idOrden = %s
        """, (numeroOrden, idOrden))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(url_for("detalle_equipo", idEquipo=idEquipo))

    cursor.close()
    conexion.close()

    return render_template(
        "nueva_reparacion.html",
        equipo=equipo,
        tecnicos=tecnicos,
        estados=estados
    )

@app.route("/reparaciones/<int:idOrden>")
def detalle_reparacion(idOrden):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # ==============================
    # DATOS DE LA ORDEN
    # ==============================

    cursor.execute("""
        SELECT
            o.idOrden,
            o.numeroOrden,
            o.fechaIngreso,
            o.fechaInicio,
            o.fechaFinalizacion,
            o.problemaInformado,
            o.observaciones,
            o.trabajoRealizado,
            o.resultadoControl,
            o.observacionesControl,
            o.prioridad,
            

            (
                SELECT d.descripcion
                FROM diagnosticos d
                WHERE d.idOrden = o.idOrden
                ORDER BY d.idDiagnostico DESC
                LIMIT 1
            ) AS diagnosticoDescripcion,

            (
                SELECT d.observaciones
                FROM diagnosticos d
                WHERE d.idOrden = o.idOrden
                ORDER BY d.idDiagnostico DESC
                LIMIT 1
            ) AS diagnosticoObservaciones,

            e.idEquipo,
            e.tipo,
            e.marca,
            e.modelo,
            e.numeroSerie,

            c.idCliente,
            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente,

            u.idUsuario AS idTecnico,
            u.nombre AS nombreTecnico,
            u.apellido AS apellidoTecnico,

            er.idEstado,
            er.nombre AS estado

        FROM ordenes_reparacion o

        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo

        INNER JOIN clientes c
            ON e.idCliente = c.idCliente

        LEFT JOIN usuarios u
            ON o.idTecnico = u.idUsuario

        INNER JOIN estados_reparacion er
            ON o.idEstado = er.idEstado

        WHERE o.idOrden = %s
    """, (idOrden,))

    reparacion = cursor.fetchone()

    if not reparacion:
        cursor.close()
        conexion.close()
        return "Orden de reparación no encontrada", 404


    # ==============================
    # OBTENER PRESUPUESTO
    # ==============================

    cursor.execute("""
        SELECT
            idPresupuesto,
            fecha,
            subtotal,
            descuento,
            total,
            estado,
            observaciones
        FROM presupuestos
        WHERE idOrden = %s
    """, (idOrden,))

    presupuesto = cursor.fetchone()


    # ==============================
    # OBTENER DETALLES DEL PRESUPUESTO
    # ==============================

    detalles_presupuesto = []

    if presupuesto:

        cursor.execute("""
            SELECT
                idDetalle,
                descripcion,
                cantidad,
                precioUnitario,
                subtotal
            FROM detalles_presupuesto
            WHERE idPresupuesto = %s
            ORDER BY idDetalle
        """, (presupuesto["idPresupuesto"],))

        detalles_presupuesto = cursor.fetchall()

 # ==============================
    # OBTENER REPUESTOS UTILIZADOS
    # ==============================

    cursor.execute("""
        SELECT
            rr.idReparacionRepuesto,
            rr.idRepuesto,
            rr.cantidad,
            rr.precioUnitario,
            rr.subtotal,
            r.codigo,
            r.nombre
        FROM repuestos_reparacion rr
        INNER JOIN repuestos r
            ON rr.idRepuesto = r.idRepuesto
        WHERE rr.idOrden = %s
        ORDER BY rr.idReparacionRepuesto
    """, (idOrden,))

    repuestos_reparacion = cursor.fetchall()


    # ==============================
    # CERRAR CONEXIÓN
    # ==============================

    cursor.close()
    conexion.close()


    # ==============================
    # MOSTRAR LA ORDEN
    # ==============================

    return render_template(
        "detalle_reparacion.html",
        reparacion=reparacion,
        presupuesto=presupuesto,
        detalles_presupuesto=detalles_presupuesto,
        repuestos_reparacion=repuestos_reparacion
    )

@app.route("/reparaciones/<int:idOrden>/estado", methods=["POST"])
def cambiar_estado_reparacion(idOrden):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    idEstado = request.form["idEstado"]

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE ordenes_reparacion
        SET idEstado = %s
        WHERE idOrden = %s
    """, (idEstado, idOrden))

    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect(url_for("detalle_reparacion", idOrden=idOrden))

@app.route("/presupuestos/<int:idPresupuesto>/aprobar", methods=["POST"])
def aprobar_presupuesto(idPresupuesto):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Obtener la orden asociada al presupuesto
    cursor.execute("""
        SELECT idOrden
        FROM presupuestos
        WHERE idPresupuesto = %s
    """, (idPresupuesto,))

    presupuesto = cursor.fetchone()

    if not presupuesto:
        cursor.close()
        conexion.close()
        return "Presupuesto no encontrado", 404

    idOrden = presupuesto["idOrden"]

    # Aprobar presupuesto
    cursor.execute("""
        UPDATE presupuestos
        SET estado = 'Aprobado'
        WHERE idPresupuesto = %s
    """, (idPresupuesto,))

    # Actualizar estado de la orden
    cursor.execute("""
        UPDATE ordenes_reparacion
        SET idEstado = 4
        WHERE idOrden = %s
    """, (idOrden,))

    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect(
        url_for("detalle_reparacion", idOrden=idOrden)
    )


@app.route("/presupuestos/<int:idPresupuesto>/rechazar", methods=["POST"])
def rechazar_presupuesto(idPresupuesto):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Obtener la orden asociada al presupuesto
    cursor.execute("""
        SELECT idOrden
        FROM presupuestos
        WHERE idPresupuesto = %s
    """, (idPresupuesto,))

    presupuesto = cursor.fetchone()

    if not presupuesto:
        cursor.close()
        conexion.close()
        return "Presupuesto no encontrado", 404

    idOrden = presupuesto["idOrden"]

    # Rechazar presupuesto
    cursor.execute("""
        UPDATE presupuestos
        SET estado = 'Rechazado'
        WHERE idPresupuesto = %s
    """, (idPresupuesto,))

    # Cancelar la orden
    cursor.execute("""
        UPDATE ordenes_reparacion
        SET idEstado = 9
        WHERE idOrden = %s
    """, (idOrden,))

    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect(
        url_for("detalle_reparacion", idOrden=idOrden)
    )

@app.route("/reparaciones/<int:idOrden>/trabajo", methods=["POST"])
def guardar_trabajo_reparacion(idOrden):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    trabajoRealizado = request.form["trabajoRealizado"].strip()

    if not trabajoRealizado:
        return "El trabajo realizado no puede estar vacío.", 400

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE ordenes_reparacion
        SET trabajoRealizado = %s,
            idEstado = 5,
            fechaInicio = COALESCE(fechaInicio, CURRENT_TIMESTAMP)
        WHERE idOrden = %s
    """, (
        trabajoRealizado,
        idOrden
    ))

    conexion.commit()

    cursor.close()
    conexion.close()

    return redirect(
        url_for("detalle_reparacion", idOrden=idOrden)
    )

@app.route("/reparaciones/<int:idOrden>/calidad", methods=["GET", "POST"])
def registrar_control_calidad(idOrden):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Obtener datos de la orden
    cursor.execute("""
        SELECT
            o.idOrden,
            o.numeroOrden,
            o.idEstado,
            o.resultadoControl,
            o.observacionesControl,
            e.tipo,
            e.marca,
            e.modelo,
            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente
        FROM ordenes_reparacion o
        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo
        INNER JOIN clientes c
            ON e.idCliente = c.idCliente
        WHERE o.idOrden = %s
    """, (idOrden,))

    reparacion = cursor.fetchone()

    if not reparacion:
        cursor.close()
        conexion.close()
        return "Orden de reparación no encontrada", 404

    # Guardar control de calidad
    if request.method == "POST":

        resultadoControl = request.form["resultadoControl"].strip()
        observacionesControl = request.form["observacionesControl"].strip()

        if not resultadoControl:
            cursor.close()
            conexion.close()
            return "El resultado del control de calidad no puede estar vacío.", 400

        cursor.execute("""
            UPDATE ordenes_reparacion
            SET
                resultadoControl = %s,
                observacionesControl = %s,
                idEstado = 6
            WHERE idOrden = %s
        """, (
            resultadoControl,
            observacionesControl,
            idOrden
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(
            url_for("detalle_reparacion", idOrden=idOrden)
        )

    cursor.close()
    conexion.close()

    return render_template(
        "control_calidad.html",
        reparacion=reparacion
    )

@app.route("/reparaciones")
def reparaciones():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            o.idOrden,
            o.numeroOrden,
            o.fechaIngreso,
            o.fechaFinalizacion,
            o.prioridad,
            o.problemaInformado,

            e.idEquipo,
            e.tipo,
            e.marca,
            e.modelo,

            c.idCliente,
            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente,

            u.nombre AS nombreTecnico,
            u.apellido AS apellidoTecnico,

            er.idEstado,
            er.nombre AS estado

        FROM ordenes_reparacion o

        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo

        INNER JOIN clientes c
            ON e.idCliente = c.idCliente

        LEFT JOIN usuarios u
            ON o.idTecnico = u.idUsuario

        INNER JOIN estados_reparacion er
            ON o.idEstado = er.idEstado

        ORDER BY o.idOrden DESC
    """)

    reparaciones = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "reparaciones.html",
        reparaciones=reparaciones
    )

@app.route("/reparaciones/<int:idOrden>/diagnostico", methods=["GET", "POST"])
def registrar_diagnostico(idOrden):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Obtener la orden y sus datos principales
    cursor.execute("""
        SELECT
            o.idOrden,
            o.numeroOrden,
            o.idTecnico,
            o.idEstado,
            e.tipo,
            e.marca,
            e.modelo,
            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente,
            u.nombre AS nombreTecnico,
            u.apellido AS apellidoTecnico
        FROM ordenes_reparacion o
        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo
        INNER JOIN clientes c
            ON e.idCliente = c.idCliente
        LEFT JOIN usuarios u
            ON o.idTecnico = u.idUsuario
        WHERE o.idOrden = %s
    """, (idOrden,))

    reparacion = cursor.fetchone()

    if not reparacion:
        cursor.close()
        conexion.close()
        return "Orden de reparación no encontrada", 404

    # Guardar diagnóstico
    if request.method == "POST":

        descripcion = request.form["descripcion"].strip()
        observaciones = request.form["observaciones"].strip()

        # Usamos el técnico asignado a la orden
        idTecnico = reparacion["idTecnico"]

        if not idTecnico:
            cursor.close()
            conexion.close()
            return "La orden no tiene un técnico asignado.", 400

        cursor.execute("""
            INSERT INTO diagnosticos
            (
                idOrden,
                idTecnico,
                descripcion,
                observaciones
            )
            VALUES (%s, %s, %s, %s)
        """, (
            idOrden,
            idTecnico,
            descripcion,
            observaciones
        ))

            # Pasar la orden a "Presupuesto pendiente"
        cursor.execute("""
            UPDATE ordenes_reparacion
            SET idEstado = 3
            WHERE idOrden = %s
        """, (idOrden,))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(
            url_for("detalle_reparacion", idOrden=idOrden)
        )

    cursor.close()
    conexion.close()

    return render_template(
        "nuevo_diagnostico.html",
        reparacion=reparacion
    )

@app.route("/reparaciones/<int:idOrden>/presupuesto", methods=["GET", "POST"])
def nuevo_presupuesto(idOrden):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Obtener datos de la orden
    cursor.execute("""
        SELECT
            o.idOrden,
            o.numeroOrden,
            o.problemaInformado,
            o.observaciones AS observacionesOrden,
            e.tipo,
            e.marca,
            e.modelo,
            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente
        FROM ordenes_reparacion o
        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo
        INNER JOIN clientes c
            ON e.idCliente = c.idCliente
        WHERE o.idOrden = %s
    """, (idOrden,))

    reparacion = cursor.fetchone()

    if not reparacion:
        cursor.close()
        conexion.close()
        return "Orden de reparación no encontrada", 404

    # Comprobar si ya existe un presupuesto
    cursor.execute("""
        SELECT
            idPresupuesto,
            fecha,
            subtotal,
            descuento,
            total,
            estado,
            observaciones
        FROM presupuestos
        WHERE idOrden = %s
    """, (idOrden,))

    presupuesto_existente = cursor.fetchone()

    if presupuesto_existente:
        cursor.close()
        conexion.close()
        return "Esta orden ya tiene un presupuesto.", 400

    # Crear presupuesto
    if request.method == "POST":

        descripcion = request.form["descripcion"].strip()
        cantidad = int(request.form["cantidad"])
        precioUnitario = float(request.form["precioUnitario"])
        descuento = float(request.form["descuento"])
        observaciones = request.form["observaciones"].strip()

        subtotalDetalle = cantidad * precioUnitario
        subtotal = subtotalDetalle
        total = subtotal - descuento

        cursor.execute("""
            INSERT INTO presupuestos
            (
                idOrden,
                subtotal,
                descuento,
                total,
                estado,
                observaciones
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            idOrden,
            subtotal,
            descuento,
            total,
            "Pendiente",
            observaciones
        ))

        idPresupuesto = cursor.lastrowid

        cursor.execute("""
            INSERT INTO detalles_presupuesto
            (
                idPresupuesto,
                descripcion,
                cantidad,
                precioUnitario,
                subtotal
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            idPresupuesto,
            descripcion,
            cantidad,
            precioUnitario,
            subtotalDetalle
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(
            url_for("detalle_reparacion", idOrden=idOrden)
        )

    cursor.close()
    conexion.close()

    return render_template(
        "nuevo_presupuesto.html",
        reparacion=reparacion
    )

@app.route("/repuestos")
def repuestos():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            idRepuesto,
            codigo,
            nombre,
            descripcion,
            stock,
            stockMinimo,
            precioCompra,
            precioVenta,
            activo
        FROM repuestos
        ORDER BY nombre
    """)

    repuestos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "repuestos.html",
        repuestos=repuestos
    )

@app.route("/reparaciones/<int:idOrden>/repuesto", methods=["GET", "POST"])
def agregar_repuesto_reparacion(idOrden):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Obtener la orden
    cursor.execute("""
        SELECT
            o.idOrden,
            o.numeroOrden,
            e.tipo,
            e.marca,
            e.modelo
        FROM ordenes_reparacion o
        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo
        WHERE o.idOrden = %s
    """, (idOrden,))

    reparacion = cursor.fetchone()

    if not reparacion:
        cursor.close()
        conexion.close()
        return "Orden de reparación no encontrada", 404

    # Repuestos activos con stock disponible
    cursor.execute("""
        SELECT
            idRepuesto,
            codigo,
            nombre,
            stock,
            precioVenta
        FROM repuestos
        WHERE activo = 1
        AND stock > 0
        ORDER BY nombre
    """)

    repuestos = cursor.fetchall()

    if request.method == "POST":

        idRepuesto = request.form["idRepuesto"]
        cantidad = int(request.form["cantidad"])

        # Obtener el repuesto seleccionado
        cursor.execute("""
            SELECT
                idRepuesto,
                nombre,
                stock,
                precioVenta
            FROM repuestos
            WHERE idRepuesto = %s
            AND activo = 1
        """, (idRepuesto,))

        repuesto = cursor.fetchone()

        if not repuesto:
            cursor.close()
            conexion.close()
            return "Repuesto no encontrado", 404

        # Verificar stock
        if cantidad > repuesto["stock"]:
            cursor.close()
            conexion.close()
            return "Stock insuficiente para el repuesto seleccionado.", 400

        precioUnitario = repuesto["precioVenta"]
        subtotal = cantidad * precioUnitario

        # Registrar repuesto utilizado
        cursor.execute("""
            INSERT INTO repuestos_reparacion
            (
                idOrden,
                idRepuesto,
                cantidad,
                precioUnitario,
                subtotal
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            idOrden,
            idRepuesto,
            cantidad,
            precioUnitario,
            subtotal
        ))

        # Descontar stock
        cursor.execute("""
            UPDATE repuestos
            SET stock = stock - %s
            WHERE idRepuesto = %s
        """, (
            cantidad,
            idRepuesto
        ))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(
            url_for("detalle_reparacion", idOrden=idOrden)
        )

    cursor.close()
    conexion.close()

    return render_template(
        "agregar_repuesto.html",
        reparacion=reparacion,
        repuestos=repuestos
    )

@app.route("/reparaciones/<int:idOrden>/entrega", methods=["GET", "POST"])
def registrar_entrega(idOrden):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # Obtener datos de la orden y el presupuesto
    cursor.execute("""
        SELECT
            o.idOrden,
            o.numeroOrden,
            o.idEstado,
            e.tipo,
            e.marca,
            e.modelo,
            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente,
            p.idPresupuesto,
            p.total,
            p.estado AS estadoPresupuesto
        FROM ordenes_reparacion o

        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo

        INNER JOIN clientes c
            ON e.idCliente = c.idCliente

        LEFT JOIN presupuestos p
            ON o.idOrden = p.idOrden

        WHERE o.idOrden = %s
    """, (idOrden,))

    reparacion = cursor.fetchone()

    if not reparacion:
        cursor.close()
        conexion.close()
        return "Orden de reparación no encontrada", 404

    # La entrega solo puede hacerse cuando está lista para retirar
    if reparacion["idEstado"] != 7:
        cursor.close()
        conexion.close()
        return "La orden todavía no está lista para retirar.", 400

    # Verificar que no exista ya una entrega
    cursor.execute("""
        SELECT idEntrega
        FROM entregas
        WHERE idOrden = %s
    """, (idOrden,))

    entrega_existente = cursor.fetchone()

    if entrega_existente:
        cursor.close()
        conexion.close()
        return "Esta orden ya tiene una entrega registrada.", 400

    # Registrar entrega
    if request.method == "POST":

        metodoPago = request.form["metodoPago"].strip()
        observaciones = request.form["observaciones"].strip()

        # Registrar entrega
        cursor.execute("""
            INSERT INTO entregas
            (
                idOrden,
                fecha,
                entregadoPor,
                observaciones
            )
            VALUES (%s, CURRENT_TIMESTAMP, %s, %s)
        """, (
            idOrden,
            session["usuario_id"],
            observaciones
        ))

        # Registrar recibo
        cursor.execute("""
            INSERT INTO recibos
            (
                idOrden,
                fecha,
                monto,
                metodoPago,
                observaciones
            )
            VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s)
        """, (
            idOrden,
            reparacion["total"],
            metodoPago,
            observaciones
        ))

        # Cambiar la orden a "Entregado"
        cursor.execute("""
            UPDATE ordenes_reparacion
            SET
                idEstado = 8,
                fechaFinalizacion = CURRENT_TIMESTAMP
            WHERE idOrden = %s
        """, (idOrden,))

        conexion.commit()

        cursor.close()
        conexion.close()

        return redirect(
            url_for("detalle_reparacion", idOrden=idOrden)
        )

    cursor.close()
    conexion.close()

    return render_template(
        "registrar_entrega.html",
        reparacion=reparacion
    )

@app.route("/presupuestos")
def presupuestos():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.idPresupuesto,
            p.idOrden,
            p.fecha,
            p.subtotal,
            p.descuento,
            p.total,
            p.estado,

            o.numeroOrden,

            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente,

            e.tipo,
            e.marca,
            e.modelo

        FROM presupuestos p

        INNER JOIN ordenes_reparacion o
            ON p.idOrden = o.idOrden

        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo

        INNER JOIN clientes c
            ON e.idCliente = c.idCliente

        ORDER BY p.idPresupuesto DESC
    """)

    presupuestos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "presupuestos.html",
        presupuestos=presupuestos
    )

@app.route("/entregas")
def entregas():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            en.idEntrega,
            en.idOrden,
            en.fecha,
            en.entregadoPor,
            en.observaciones,

            o.numeroOrden,

            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente,

            e.tipo,
            e.marca,
            e.modelo,

            u.nombre AS nombreUsuario,
            u.apellido AS apellidoUsuario

        FROM entregas en

        INNER JOIN ordenes_reparacion o
            ON en.idOrden = o.idOrden

        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo

        INNER JOIN clientes c
            ON e.idCliente = c.idCliente

        LEFT JOIN usuarios u
            ON en.entregadoPor = u.idUsuario

        ORDER BY en.idEntrega DESC
    """)

    entregas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "entregas.html",
        entregas=entregas
    )

@app.route("/reportes")
def reportes():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # ==============================
    # TOTALES GENERALES
    # ==============================

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM clientes
    """)
    total_clientes = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM equipos
    """)
    total_equipos = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM ordenes_reparacion
    """)
    total_ordenes = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM ordenes_reparacion o
        INNER JOIN estados_reparacion e
            ON o.idEstado = e.idEstado
        WHERE e.nombre = 'Entregado'
    """)
    total_entregadas = cursor.fetchone()["total"]


    # ==============================
    # ÓRDENES POR ESTADO
    # ==============================

    cursor.execute("""
        SELECT
            e.nombre AS estado,
            COUNT(o.idOrden) AS cantidad
        FROM estados_reparacion e
        LEFT JOIN ordenes_reparacion o
            ON e.idEstado = o.idEstado
        GROUP BY e.idEstado, e.nombre
        ORDER BY e.idEstado
    """)

    ordenes_por_estado = cursor.fetchall()


    # ==============================
    # STOCK BAJO
    # ==============================

    cursor.execute("""
        SELECT
            idRepuesto,
            codigo,
            nombre,
            stock,
            stockMinimo
        FROM repuestos
        WHERE activo = 1
        AND stock <= stockMinimo
        ORDER BY stock ASC, nombre
    """)

    stock_bajo = cursor.fetchall()


    cursor.close()
    conexion.close()

    return render_template(
        "reportes.html",
        total_clientes=total_clientes,
        total_equipos=total_equipos,
        total_ordenes=total_ordenes,
        total_entregadas=total_entregadas,
        ordenes_por_estado=ordenes_por_estado,
        stock_bajo=stock_bajo
    )

@app.route("/diagnosticos")
def diagnosticos():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            d.idDiagnostico,
            d.idOrden,
            d.fecha,
            d.descripcion,
            d.observaciones,

            o.numeroOrden,

            c.nombre AS nombreCliente,
            c.apellido AS apellidoCliente,

            e.tipo,
            e.marca,
            e.modelo,

            u.nombre AS nombreTecnico,
            u.apellido AS apellidoTecnico

        FROM diagnosticos d

        INNER JOIN ordenes_reparacion o
            ON d.idOrden = o.idOrden

        INNER JOIN equipos e
            ON o.idEquipo = e.idEquipo

        INNER JOIN clientes c
            ON e.idCliente = c.idCliente

        LEFT JOIN usuarios u
            ON d.idTecnico = u.idUsuario

        ORDER BY d.idDiagnostico DESC
    """)

    diagnosticos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "diagnosticos.html",
        diagnosticos=diagnosticos
    )

@app.route("/panel")
def panel():

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "panel.html",
        nombre=session["nombre"]
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)

    