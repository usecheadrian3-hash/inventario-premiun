from flask import Flask, render_template, request, redirect, session, jsonify
import re, os, hashlib, secrets, json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from db import cursor, conexion, _conectar, DB_FILE

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "inventario_secreto_2024_mejorado")
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def registrar_historial(usuario_id, usuario_nombre, accion, detalle, tabla=None, reg_id=None):
    try:
        cursor.execute(
            "INSERT INTO historial (usuario_id, usuario_nombre, accion, detalle, tabla_afectada, registro_id) VALUES (%s,%s,%s,%s,%s,%s)",
            (usuario_id, usuario_nombre, accion, detalle, tabla, reg_id)
        )
        conexion.commit()
    except:
        pass

def registrar_actividad(usuario_id, usuario_nombre, accion, detalle):
    try:
        ip = request.remote_addr or '0.0.0.0'
        cursor.execute(
            "INSERT INTO actividad (usuario_id, usuario_nombre, accion, detalle, ip_address) VALUES (%s,%s,%s,%s,%s)",
            (usuario_id, usuario_nombre, accion, detalle, ip)
        )
        conexion.commit()
    except:
        pass

def crear_tablas():
    cursor.execute("""CREATE TABLE IF NOT EXISTS comentarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre VARCHAR(100), texto TEXT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, usuario_nombre VARCHAR(200),
        accion VARCHAR(50), detalle TEXT, tabla_afectada VARCHAR(100),
        registro_id INTEGER, fecha DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS actividad (
        id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, usuario_nombre VARCHAR(200),
        accion VARCHAR(100), detalle TEXT, ip_address VARCHAR(50),
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre VARCHAR(200), contacto VARCHAR(200),
        telefono VARCHAR(50), correo VARCHAR(200), direccion TEXT,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre VARCHAR(100) UNIQUE, descripcion TEXT)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS etiquetas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre VARCHAR(100) UNIQUE)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre VARCHAR(200), telefono VARCHAR(50),
        correo VARCHAR(200), direccion TEXT, total_compras NUMERIC DEFAULT 0,
        visitas INTEGER DEFAULT 0, ultima_compra DATETIME,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, usuario_nombre VARCHAR(200),
        cliente_id INTEGER, cliente_nombre VARCHAR(200), total NUMERIC,
        iva_total NUMERIC, subtotal NUMERIC, metodo_pago VARCHAR(50),
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS detalle_ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, producto_id INTEGER,
        producto_nombre VARCHAR(200), cantidad INTEGER, precio_unitario NUMERIC,
        iva NUMERIC, subtotal NUMERIC)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, descripcion TEXT, monto NUMERIC,
        categoria VARCHAR(100), usuario_id INTEGER, fecha DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT, producto_id INTEGER, producto_nombre VARCHAR(200),
        cantidad INTEGER, precio_unitario NUMERIC, total NUMERIC,
        proveedor_id INTEGER, usuario_id INTEGER, fecha DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS recuperacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, token VARCHAR(255),
        usado BOOLEAN DEFAULT FALSE, fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_uso DATETIME)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre VARCHAR(200), apellido VARCHAR(200),
        correo VARCHAR(200) UNIQUE, password VARCHAR(300),
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        rol VARCHAR(50) DEFAULT 'empleado', foto VARCHAR(500),
        verificado BOOLEAN DEFAULT FALSE, activo BOOLEAN DEFAULT TRUE,
        ultimo_acceso DATETIME, permisos TEXT)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nombre VARCHAR(200), descripcion TEXT,
        cantidad INTEGER DEFAULT 0, stock_minimo INTEGER DEFAULT 0, precio NUMERIC,
        categoria VARCHAR(100), proveedor VARCHAR(200), fecha DATE,
        estado VARCHAR(50) DEFAULT 'Activo',
        iva NUMERIC DEFAULT 19.00, etiquetas VARCHAR(500) DEFAULT '',
        precio_con_iva NUMERIC GENERATED ALWAYS AS (precio + (precio * iva / 100)) STORED)""")

    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN rol VARCHAR(50) DEFAULT 'empleado'")
    except: pass
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN foto VARCHAR(500) DEFAULT NULL")
    except: pass
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN verificado BOOLEAN DEFAULT FALSE")
    except: pass
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN activo BOOLEAN DEFAULT TRUE")
    except: pass
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN ultimo_acceso DATETIME")
    except: pass
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP")
    except: pass
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN iva NUMERIC DEFAULT 19.00")
    except: pass
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN precio_con_iva NUMERIC GENERATED ALWAYS AS (precio + (precio * iva / 100)) STORED")
    except:
        try:
            cursor.execute("ALTER TABLE productos ADD COLUMN precio_con_iva NUMERIC DEFAULT 0")
        except: pass
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN etiquetas VARCHAR(500) DEFAULT ''")
    except: pass
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN permisos TEXT DEFAULT NULL")
    except: pass
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        admin_hash = hashlib.sha256(b"Admin123!").hexdigest()
        cursor.execute(
            "INSERT INTO usuarios (nombre, apellido, correo, password, rol, activo, verificado) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            ("Admin", "Inventario", "admin@inventario.com", admin_hash, "admin", 1, 1),
        )
        print("[setup] Usuario admin creado: admin@inventario.com / Admin123!", flush=True)
    conexion.commit()

_tablas_creadas = False

def _ini():
    global _tablas_creadas
    if not _tablas_creadas:
        try:
            crear_tablas()
            _tablas_creadas = True
        except Exception as e:
            print("[WARN] DB init failed:", e, flush=True)

@app.before_request
def _init_once():
    _ini()

@app.route("/debug")
def debug_env():
    import platform, traceback
    lines = ["<h1>Debug</h1><pre>"]
    for k, v in sorted(os.environ.items()):
        if any(x in k.lower() for x in ["mysql", "db_", "port", "host", "user", "pass", "secret", "database"]):
            lines.append(f"{k} = {v}")
    lines.append(f"\nDB_FILE = {DB_FILE}")
    lines.append(f"\nPython: {platform.python_version()}")
    try:
        cur = _conectar().cursor()
        lines.append("\n✅ Conexión SQLite EXITOSA")
        cur.execute("SELECT sqlite_version()")
        v = cur.fetchone()
        lines.append(f"SQLite version: {v[0]}")
        cur.close()
    except Exception as e:
        lines.append(f"\n❌ Error de conexión BD: {str(e)}")
        lines.append(traceback.format_exc())
    lines.append("</pre>")
    return "".join(lines)

def tiene_permiso(permiso):
    if 'usuario_id' not in session:
        return False
    if session.get('usuario_rol') == 'admin':
        return True
    try:
        cursor.execute("SELECT permisos FROM usuarios WHERE id=%s", (session['usuario_id'],))
        r = cursor.fetchone()
        if r and r[0]:
            perms = r[0].split(',')
            return permiso in perms
    except: pass
    return False

def requerir_permiso(permiso):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not tiene_permiso(permiso):
                return redirect('/')
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def obtener_productos_con_iva():
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    has_col = None
    try:
        cursor.execute("PRAGMA table_info(productos)")
        cols = cursor.fetchall()
        if any(row[1] == "precio_con_iva" for row in cols):
            has_col = True
    except:
        has_col = None
    return productos, has_col is not None

# ==================== RUTAS EXISTENTES (MEJORADAS) ====================

@app.route("/")
def inicio():
    return render_template("portada.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            correo = request.form["correo"]
            password = hashlib.sha256(request.form["password"].encode()).hexdigest()
            cursor.execute("SELECT * FROM usuarios WHERE correo=%s AND password=%s", (correo, password))
            usuario = cursor.fetchone()
            if usuario:
                if not usuario[9]:
                    return render_template("index.html", error="Cuenta desactivada. Contacta al administrador.")
                session["usuario_id"] = usuario[0]
                session["usuario_nombre"] = usuario[1]
                session["usuario_rol"] = usuario[6]
                cursor.execute("UPDATE usuarios SET ultimo_acceso=NOW() WHERE id=%s", (usuario[0],))
                conexion.commit()
                registrar_actividad(usuario[0], usuario[1], "Inicio de sesión", f"Login exitoso - Rol: {usuario[6]}")
                return redirect("/blog")
            else:
                return render_template("index.html", error="Correo o contraseña incorrectos")
        except Exception as e:
            return render_template("index.html", error=f"Error de conexión a la BD: {str(e)}")
    return render_template("index.html")

@app.route("/registro")
def registro():
    return render_template("registro.html")

@app.route("/guardar", methods=["POST"])
def guardar():
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]
    correo = request.form["correo"]
    password = request.form["password"]
    confirmar = request.form["confirmar"]
    rol = request.form.get("rol", "empleado")

    if password != confirmar:
        return render_template("registro.html", error="Las contraseñas no coinciden", form_data=request.form)
    if not re.match(r'^[\w\.-]+@gmail\.com$', correo):
        return render_template("registro.html", error="Debe ser un correo Gmail", form_data=request.form)
    if len(password) < 6:
        return render_template("registro.html", error="La contraseña debe tener al menos 6 caracteres", form_data=request.form)

    cursor.execute("SELECT id FROM usuarios WHERE correo=%s", (correo,))
    if cursor.fetchone():
        return render_template("registro.html", error="Este correo ya está registrado", form_data=request.form)

    hash_pass = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute(
            "INSERT INTO usuarios (nombre, apellido, correo, password, rol) VALUES (%s,%s,%s,%s,%s)",
            (nombre, apellido, correo, hash_pass, rol)
        )
        conexion.commit()
        uid = cursor.lastrowid
        registrar_historial(uid, nombre, "Registro", f"Nuevo usuario registrado como {rol}")
        return redirect("/login")
    except Exception as e:
        return render_template("registro.html", error=f"Error al registrar: {str(e)}", form_data=request.form)

@app.route("/perfil")
def perfil():
    if "usuario_id" not in session:
        return redirect("/login")
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    return render_template("perfil.html", usuario=usuario)

@app.route("/blog")
def blog():
    if "usuario_id" not in session:
        return redirect("/login")
    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    cursor.execute("SELECT * FROM categorias ORDER BY nombre")
    categorias = cursor.fetchall()
    cursor.execute("SELECT * FROM proveedores ORDER BY nombre")
    proveedores = cursor.fetchall()
    cursor.execute("SELECT * FROM etiquetas ORDER BY nombre")
    etiquetas = cursor.fetchall()
    cursor.execute("SELECT SUM(total) FROM ventas")
    ventas_total = cursor.fetchone()[0] or 0
    return render_template("blog.html", productos=productos, usuario=usuario,
                          categorias=categorias, proveedores=proveedores, etiquetas=etiquetas,
                          ventas_total=ventas_total)

# ==================== CRUD PRODUCTOS (MEJORADO CON IVA) ====================

@app.route("/agregar_producto", methods=["POST"])
def agregar_producto():
    if "usuario_id" not in session:
        return redirect("/login")
    iva_val = float(request.form.get("iva", 19))
    cursor.execute(
        """INSERT INTO productos
        (nombre, descripcion, cantidad, stock_minimo, precio, categoria, proveedor, fecha, estado, iva, etiquetas)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            request.form["nombre"], request.form["descripcion"],
            request.form["cantidad"], request.form["stock_minimo"],
            request.form["precio"], request.form["categoria"],
            request.form["proveedor"], request.form["fecha"],
            request.form["estado"], iva_val, request.form.get("etiquetas", "")
        )
    )
    conexion.commit()
    registrar_historial(session["usuario_id"], session["usuario_nombre"], "Agregar",
                       f"Producto: {request.form['nombre']}", "productos", cursor.lastrowid)
    registrar_actividad(session["usuario_id"], session["usuario_nombre"], "Agregar producto",
                       f"Producto: {request.form['nombre']} - ${request.form['precio']}")
    return redirect("/blog")

@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    if "usuario_id" not in session:
        return redirect("/login")
    iva_val = float(request.form.get("iva", 19))
    cursor.execute(
        """UPDATE productos SET nombre=%s, descripcion=%s, cantidad=%s, stock_minimo=%s,
        precio=%s, categoria=%s, proveedor=%s, fecha=%s, estado=%s, iva=%s, etiquetas=%s
        WHERE id=%s""",
        (request.form["nombre"], request.form["descripcion"], request.form["cantidad"],
         request.form["stock_minimo"], request.form["precio"], request.form["categoria"],
         request.form["proveedor"], request.form["fecha"], request.form["estado"],
         iva_val, request.form.get("etiquetas", ""), id)
    )
    conexion.commit()
    registrar_historial(session["usuario_id"], session["usuario_nombre"], "Editar",
                       f"Producto ID {id}: {request.form['nombre']}", "productos", id)
    registrar_actividad(session["usuario_id"], session["usuario_nombre"], "Editar producto",
                       f"Producto ID {id} editado")
    return redirect("/blog")

@app.route("/eliminar/<int:id>")
def eliminar(id):
    if "usuario_id" not in session:
        return redirect("/login")
    cursor.execute("SELECT nombre FROM productos WHERE id=%s", (id,))
    prod = cursor.fetchone()
    nom = prod[0] if prod else "Desconocido"
    cursor.execute("DELETE FROM productos WHERE id=%s", (id,))
    conexion.commit()
    registrar_historial(session["usuario_id"], session["usuario_nombre"], "Eliminar",
                       f"Producto ID {id}: {nom}", "productos", id)
    registrar_actividad(session["usuario_id"], session["usuario_nombre"], "Eliminar producto",
                       f"Producto ID {id} eliminado")
    return redirect("/blog")

# ==================== COMENTARIOS ====================

@app.route("/comentarios")
def comentarios():
    cursor.execute("SELECT * FROM comentarios ORDER BY fecha DESC")
    comentarios = cursor.fetchall()
    return render_template("comentarios.html", comentarios=comentarios)

@app.route("/guardar_comentario", methods=["POST"])
def guardar_comentario():
    nombre = request.form["nombre"]
    texto = request.form["texto"]
    cursor.execute("INSERT INTO comentarios (nombre, texto) VALUES (%s, %s)", (nombre, texto))
    conexion.commit()
    return redirect("/comentarios")

@app.route("/logout")
def logout():
    if "usuario_id" in session:
        registrar_actividad(session["usuario_id"], session["usuario_nombre"], "Cierre de sesión", "Logout")
    session.clear()
    return redirect("/")

# ==================== PROVEEDORES ====================

@app.route("/proveedores")
def ver_proveedores():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("SELECT * FROM proveedores ORDER BY nombre")
    proveedores = cursor.fetchall()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    return render_template("proveedores.html", proveedores=proveedores, usuario=usuario)

@app.route("/agregar_proveedor", methods=["POST"])
def agregar_proveedor():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("INSERT INTO proveedores (nombre, contacto, telefono, correo, direccion) VALUES (%s,%s,%s,%s,%s)",
                   (request.form["nombre"], request.form["contacto"], request.form["telefono"],
                    request.form["correo"], request.form["direccion"]))
    conexion.commit()
    registrar_actividad(session["usuario_id"], session["usuario_nombre"], "Agregar proveedor",
                       f"Proveedor: {request.form['nombre']}")
    return redirect("/proveedores")

@app.route("/editar_proveedor/<int:id>", methods=["POST"])
def editar_proveedor(id):
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("UPDATE proveedores SET nombre=%s, contacto=%s, telefono=%s, correo=%s, direccion=%s WHERE id=%s",
                   (request.form["nombre"], request.form["contacto"], request.form["telefono"],
                    request.form["correo"], request.form["direccion"], id))
    conexion.commit()
    return redirect("/proveedores")

@app.route("/eliminar_proveedor/<int:id>")
def eliminar_proveedor(id):
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("DELETE FROM proveedores WHERE id=%s", (id,))
    conexion.commit()
    return redirect("/proveedores")

# ==================== CATEGORÍAS ====================

@app.route("/categorias")
def ver_categorias():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("SELECT * FROM categorias ORDER BY nombre")
    categorias = cursor.fetchall()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    return render_template("categorias.html", categorias=categorias, usuario=usuario)

@app.route("/agregar_categoria", methods=["POST"])
def agregar_categoria():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("INSERT INTO categorias (nombre, descripcion) VALUES (%s,%s)",
                   (request.form["nombre"], request.form["descripcion"]))
    conexion.commit()
    return redirect("/categorias")

@app.route("/eliminar_categoria/<int:id>")
def eliminar_categoria(id):
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("DELETE FROM categorias WHERE id=%s", (id,))
    conexion.commit()
    return redirect("/categorias")

# ==================== CLIENTES ====================

@app.route("/clientes")
def ver_clientes():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("SELECT * FROM clientes ORDER BY total_compras DESC")
    clientes = cursor.fetchall()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    return render_template("clientes.html", clientes=clientes, usuario=usuario)

@app.route("/agregar_cliente", methods=["POST"])
def agregar_cliente():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("INSERT INTO clientes (nombre, telefono, correo, direccion) VALUES (%s,%s,%s,%s)",
                   (request.form["nombre"], request.form["telefono"],
                    request.form["correo"], request.form["direccion"]))
    conexion.commit()
    return redirect("/clientes")

@app.route("/eliminar_cliente/<int:id>")
def eliminar_cliente(id):
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("DELETE FROM clientes WHERE id=%s", (id,))
    conexion.commit()
    return redirect("/clientes")

# ==================== VENTAS ====================

@app.route("/ventas")
def ver_ventas():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC")
    ventas = cursor.fetchall()
    cursor.execute("SELECT * FROM clientes ORDER BY nombre")
    clientes = cursor.fetchall()
    cursor.execute("SELECT * FROM productos WHERE cantidad > 0 AND estado='Activo' ORDER BY nombre")
    productos = cursor.fetchall()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    return render_template("ventas.html", ventas=ventas, clientes=clientes,
                          productos=productos, usuario=usuario)

@app.route("/registrar_venta", methods=["POST"])
def registrar_venta():
    if "usuario_id" not in session: return redirect("/login")
    data = request.get_json()
    items = data.get('items', [])
    cliente_id = data.get('cliente_id')
    metodo = data.get('metodo_pago', 'Efectivo')
    if not items:
        return jsonify({'error': 'Sin productos'}), 400
    subtotal = 0
    iva_total = 0
    for item in items:
        cursor.execute("SELECT precio, iva, nombre FROM productos WHERE id=%s", (item['producto_id'],))
        p = cursor.fetchone()
        if not p: continue
        precio, iva, nombre = p
        if int(item['cantidad']) > 0:
            cursor.execute("UPDATE productos SET cantidad = cantidad - %s WHERE id=%s AND cantidad >= %s",
                          (int(item['cantidad']), item['producto_id'], int(item['cantidad'])))
    cursor.execute("SELECT SUM(precio * cantidad), SUM(precio * iva / 100 * cantidad) FROM productos WHERE id IN ({})".format(
        ','.join(str(x['producto_id']) for x in items)), [])
    calc = cursor.fetchone()
    subtotal = data.get('subtotal', 0)
    iva_total = data.get('iva_total', 0)
    total = float(subtotal) + float(iva_total)
    cliente_nombre = data.get('cliente_nombre', 'Cliente General')
    cursor.execute(
        "INSERT INTO ventas (usuario_id, usuario_nombre, cliente_id, cliente_nombre, total, iva_total, subtotal, metodo_pago) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (session['usuario_id'], session['usuario_nombre'], cliente_id or 0, cliente_nombre, total, iva_total, subtotal, metodo)
    )
    venta_id = cursor.lastrowid
    for item in items:
        cursor.execute("SELECT nombre FROM productos WHERE id=%s", (item['producto_id'],))
        p = cursor.fetchone()
        if not p: continue
        cursor.execute(
            "INSERT INTO detalle_ventas (venta_id, producto_id, producto_nombre, cantidad, precio_unitario, iva, subtotal) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (venta_id, item['producto_id'], p[0], int(item['cantidad']),
             float(item['precio']), float(item.get('iva', 19)), float(item['subtotal']))
        )
    conexion.commit()
    if cliente_id:
        cursor.execute("UPDATE clientes SET total_compras = total_compras + %s, visitas = visitas + 1, ultima_compra = NOW() WHERE id=%s",
                      (total, cliente_id))
        conexion.commit()
    registrar_historial(session["usuario_id"], session["usuario_nombre"], "Venta",
                       f"Venta #{venta_id} - Total: ${total:.2f}", "ventas", venta_id)
    registrar_actividad(session["usuario_id"], session["usuario_nombre"], "Nueva venta",
                       f"Venta #{venta_id} por ${total:.2f}")
    return jsonify({'success': True, 'venta_id': venta_id, 'total': total})

@app.route("/detalle_venta/<int:id>")
def detalle_venta(id):
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("SELECT * FROM ventas WHERE id=%s", (id,))
    venta = cursor.fetchone()
    cursor.execute("SELECT * FROM detalle_ventas WHERE venta_id=%s", (id,))
    detalles = cursor.fetchall()
    return jsonify({'venta': venta, 'detalles': detalles})

# ==================== COMPRAS ====================

@app.route("/compras")
def ver_compras():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("SELECT * FROM compras ORDER BY fecha DESC")
    compras = cursor.fetchall()
    cursor.execute("SELECT * FROM productos ORDER BY nombre")
    productos = cursor.fetchall()
    cursor.execute("SELECT * FROM proveedores ORDER BY nombre")
    proveedores = cursor.fetchall()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    return render_template("compras.html", compras=compras, productos=productos,
                          proveedores=proveedores, usuario=usuario)

@app.route("/agregar_compra", methods=["POST"])
def agregar_compra():
    if "usuario_id" not in session: return redirect("/login")
    producto_id = request.form["producto_id"]
    cantidad = int(request.form["cantidad"])
    precio = float(request.form["precio_unitario"])
    total = cantidad * precio
    cursor.execute("SELECT nombre FROM productos WHERE id=%s", (producto_id,))
    p = cursor.fetchone()
    nom = p[0] if p else "N/A"
    cursor.execute("UPDATE productos SET cantidad = cantidad + %s WHERE id=%s", (cantidad, producto_id))
    cursor.execute("INSERT INTO compras (producto_id, producto_nombre, cantidad, precio_unitario, total, proveedor_id, usuario_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                   (producto_id, nom, cantidad, precio, total, request.form.get("proveedor_id") or 0, session["usuario_id"]))
    conexion.commit()
    return redirect("/compras")

# ==================== GASTOS ====================

@app.route("/gastos")
def ver_gastos():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("SELECT * FROM gastos ORDER BY fecha DESC")
    gastos = cursor.fetchall()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    return render_template("gastos.html", gastos=gastos, usuario=usuario)

@app.route("/agregar_gasto", methods=["POST"])
def agregar_gasto():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("INSERT INTO gastos (descripcion, monto, categoria, usuario_id) VALUES (%s,%s,%s,%s)",
                   (request.form["descripcion"], request.form["monto"],
                    request.form["categoria"], session["usuario_id"]))
    conexion.commit()
    return redirect("/gastos")

# ==================== ADMIN PANEL ====================

@app.route("/admin")
def admin_panel():
    if "usuario_id" not in session or session.get("usuario_rol") != "admin":
        return redirect("/")
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    cursor.execute("SELECT * FROM usuarios ORDER BY id")
    usuarios = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM productos")
    total_productos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM productos WHERE cantidad <= stock_minimo OR cantidad = 0")
    productos_agotados = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ventas")
    total_ventas = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(total) FROM ventas")
    ventas_total = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM actividad WHERE fecha >= DATE_SUB(NOW(), INTERVAL 1 HOUR)")
    conectados = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(monto) FROM gastos")
    total_gastos = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(total) FROM compras")
    total_compras = cursor.fetchone()[0] or 0
    ganancias = ventas_total - total_gastos - total_compras
    cursor.execute("SELECT * FROM actividad ORDER BY fecha DESC LIMIT 20")
    actividad = cursor.fetchall()
    return render_template("admin.html", usuario=usuario, usuarios=usuarios,
                          total_usuarios=total_usuarios, total_productos=total_productos,
                          productos_agotados=productos_agotados, total_ventas=total_ventas,
                          ventas_total=ventas_total, conectados=conectados,
                          total_gastos=total_gastos, total_compras=total_compras,
                          ganancias=ganancias, actividad=actividad)

@app.route("/admin/usuarios")
def admin_usuarios():
    if "usuario_id" not in session or session.get("usuario_rol") != "admin":
        return redirect("/")
    cursor.execute("SELECT * FROM usuarios ORDER BY id")
    usuarios = cursor.fetchall()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    return render_template("admin_usuarios.html", usuarios=usuarios, usuario=usuario)

@app.route("/admin/actualizar_usuario/<int:id>", methods=["POST"])
def actualizar_usuario(id):
    if "usuario_id" not in session or session.get("usuario_rol") != "admin":
        return redirect("/")
    rol = request.form["rol"]
    activo = 1 if request.form.get("activo") == "on" else 0
    cursor.execute("UPDATE usuarios SET rol=%s, activo=%s WHERE id=%s", (rol, activo, id))
    conexion.commit()
    registrar_historial(session["usuario_id"], session["usuario_nombre"], "Admin",
                       f"Usuario ID {id} actualizado: rol={rol}, activo={activo}", "usuarios", id)
    return redirect("/admin/usuarios")

@app.route("/admin/eliminar_usuario/<int:id>")
def admin_eliminar_usuario(id):
    if "usuario_id" not in session or session.get("usuario_rol") != "admin":
        return redirect("/")
    if id == session["usuario_id"]:
        return redirect("/admin/usuarios")
    cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
    conexion.commit()
    return redirect("/admin/usuarios")

@app.route("/admin/historial")
def admin_historial():
    if "usuario_id" not in session or session.get("usuario_rol") != "admin":
        return redirect("/")
    cursor.execute("SELECT * FROM historial ORDER BY fecha DESC LIMIT 100")
    historial = cursor.fetchall()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    return render_template("admin_historial.html", historial=historial, usuario=usuario)

@app.route("/admin/actividad")
def admin_actividad():
    if "usuario_id" not in session or session.get("usuario_rol") != "admin":
        return redirect("/")
    cursor.execute("SELECT * FROM actividad ORDER BY fecha DESC LIMIT 50")
    actividad = cursor.fetchall()
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    return render_template("admin_actividad.html", actividad=actividad, usuario=usuario)

# ==================== REPORTES / DATA API ====================

@app.route("/api/dashboard_data")
def api_dashboard_data():
    if "usuario_id" not in session: return jsonify({})
    cursor.execute("SELECT nombre, cantidad FROM productos ORDER BY cantidad DESC LIMIT 10")
    top_productos = cursor.fetchall()
    cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
    ventas_30d = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
    ventas_7d = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(monto) FROM gastos WHERE fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
    gastos_30d = cursor.fetchone()[0] or 0
    cursor.execute("SELECT DATE(fecha) as d, SUM(total) as t FROM ventas WHERE fecha >= DATE_SUB(NOW(), INTERVAL 7 DAY) GROUP BY DATE(fecha) ORDER BY d")
    ventas_diarias = cursor.fetchall()
    cursor.execute("SELECT p.nombre, SUM(dv.cantidad) as total_vendido FROM detalle_ventas dv JOIN productos p ON dv.producto_id=p.id GROUP BY dv.producto_id ORDER BY total_vendido DESC LIMIT 5")
    mas_vendidos = cursor.fetchall()
    cursor.execute("SELECT p.nombre, SUM(dv.cantidad) as total_vendido FROM detalle_ventas dv JOIN productos p ON dv.producto_id=p.id GROUP BY dv.producto_id ORDER BY total_vendido ASC LIMIT 5")
    menos_vendidos = cursor.fetchall()
    cursor.execute("SELECT nombre, precio FROM productos ORDER BY precio DESC LIMIT 5")
    caros = cursor.fetchall()
    return jsonify({
        'top_productos': top_productos,
        'ventas_30d': ventas_30d,
        'ventas_7d': ventas_7d,
        'gastos_30d': gastos_30d,
        'ventas_diarias': ventas_diarias,
        'mas_vendidos': mas_vendidos,
        'menos_vendidos': menos_vendidos,
        'productos_caros': caros
    })

@app.route("/api/reporte_general")
def api_reporte_general():
    if "usuario_id" not in session: return jsonify({})
    cursor.execute("SELECT COUNT(*), SUM(cantidad), AVG(precio), SUM(precio*cantidad) FROM productos")
    res = cursor.fetchone()
    cursor.execute("SELECT COUNT(*), SUM(total) FROM ventas")
    v = cursor.fetchone()
    cursor.execute("SELECT COUNT(*), SUM(monto) FROM gastos")
    g = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM clientes")
    c = cursor.fetchone()[0]
    return jsonify({
        'productos': {'total': res[0] or 0, 'stock': res[1] or 0, 'precio_promedio': float(res[2] or 0), 'valor_total': float(res[3] or 0)},
        'ventas': {'total': v[0] or 0, 'monto': float(v[1] or 0)},
        'gastos': {'total': g[0] or 0, 'monto': float(g[1] or 0)},
        'clientes': c
    })

# ==================== DASHBOARD PREMIUM ====================

@app.route("/dashboard-premium")
def dashboard_premium():
    if "usuario_id" not in session:
        return redirect("/login")
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM productos")
    total_productos = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM productos WHERE cantidad = 0")
    agotados = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM productos WHERE cantidad > 0 AND cantidad <= stock_minimo")
    poco_stock = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT p.nombre, SUM(dv.cantidad) as total_vendido
        FROM detalle_ventas dv JOIN productos p ON dv.producto_id = p.id
        GROUP BY dv.producto_id ORDER BY total_vendido DESC LIMIT 5
    """)
    mas_vendidos = cursor.fetchall()

    cursor.execute("SELECT SUM(total) FROM ventas WHERE DATE(fecha) = CURDATE()")
    ventas_hoy = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(total) FROM ventas WHERE DATE(fecha) = CURDATE()")
    ventas_hoy = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(total) FROM ventas")
    ventas_total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(monto) FROM gastos")
    total_gastos = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(total) FROM compras")
    total_compras = cursor.fetchone()[0] or 0

    ganancias = ventas_total - total_gastos - total_compras

    cursor.execute("SELECT SUM(monto) FROM gastos WHERE DATE(fecha) = CURDATE()")
    gastos_hoy = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM actividad WHERE fecha >= DATE_SUB(NOW(), INTERVAL 1 HOUR)")
    conectados = cursor.fetchone()[0] or 0

    cursor.execute("SELECT * FROM actividad ORDER BY fecha DESC LIMIT 20")
    raw_actividad = cursor.fetchall()
    actividad = []
    for a in raw_actividad:
        lst = list(a)
        if hasattr(lst[5], 'strftime'):
            lst[5] = lst[5].strftime('%H:%M')
        else:
            lst[5] = str(lst[5])[11:16] if len(str(lst[5])) > 16 else ''
        actividad.append(tuple(lst))

    cursor.execute("SELECT * FROM historial ORDER BY fecha DESC LIMIT 20")
    raw_historial = cursor.fetchall()
    historial = []
    for h in raw_historial:
        lst = list(h)
        if len(lst) > 7 and hasattr(lst[7], 'strftime'):
            lst[7] = lst[7].strftime('%H:%M')
        elif len(lst) > 7:
            lst[7] = str(lst[7])[11:16] if len(str(lst[7])) > 16 else ''
        historial.append(tuple(lst))

    cursor.execute("""
        SELECT DATE_FORMAT(fecha, '%%Y-%%m') as mes, SUM(total) as total
        FROM ventas GROUP BY mes ORDER BY mes LIMIT 12
    """)
    ventas_mensuales = cursor.fetchall()
    ventas_mensuales_labels = json.dumps([r[0] for r in ventas_mensuales])
    ventas_mensuales_data = json.dumps([float(r[1]) for r in ventas_mensuales])

    cursor.execute("""
        SELECT categoria, COUNT(*) as total FROM productos
        WHERE categoria IS NOT NULL AND categoria != ''
        GROUP BY categoria ORDER BY total DESC
    """)
    categorias_dist = cursor.fetchall()
    categorias_dist_labels = json.dumps([r[0] for r in categorias_dist])
    categorias_dist_data = json.dumps([r[1] for r in categorias_dist])

    cursor.execute("""
        SELECT DATE(fecha) as d, SUM(total) as t
        FROM ventas WHERE fecha >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(fecha) ORDER BY d
    """)
    ventas_semana = cursor.fetchall()
    ventas_semana_labels = json.dumps([str(r[0]) for r in ventas_semana])
    ventas_semana_data = json.dumps([float(r[1]) for r in ventas_semana])

    cursor.execute("SELECT SUM(precio_con_iva * cantidad) FROM productos")
    valor_inventario = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM ventas WHERE DATE(fecha) = CURDATE()")
    num_ventas_hoy = cursor.fetchone()[0] or 0

    now = datetime.now()

    return render_template("dashboard_premium.html",
        usuario=usuario,
        now=now,
        total_productos=total_productos,
        agotados=agotados,
        poco_stock=poco_stock,
        mas_vendidos=mas_vendidos,
        ventas_hoy=ventas_hoy,
        ganancias=ganancias,
        gastos_hoy=gastos_hoy,
        conectados=conectados,
        actividad=actividad,
        historial=historial,
        ventas_mensuales_labels=ventas_mensuales_labels,
        ventas_mensuales_data=ventas_mensuales_data,
        categorias_dist_labels=categorias_dist_labels,
        categorias_dist_data=categorias_dist_data,
        ventas_semana_labels=ventas_semana_labels,
        ventas_semana_data=ventas_semana_data,
        valor_inventario=valor_inventario,
        num_ventas_hoy=num_ventas_hoy,
        total_gastos=total_gastos,
        total_compras=total_compras,
        ventas_total=ventas_total
    )

# ==================== REPORTES EMPRESARIALES ====================

@app.route("/reportes")
def reportes():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("SELECT * FROM usuarios WHERE id=%s", (session["usuario_id"],))
    usuario = cursor.fetchone()
    cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC LIMIT 50")
    ventas = cursor.fetchall()
    cursor.execute("SELECT * FROM gastos ORDER BY fecha DESC LIMIT 50")
    gastos = cursor.fetchall()
    cursor.execute("SELECT * FROM compras ORDER BY fecha DESC LIMIT 50")
    compras = cursor.fetchall()
    return render_template("reportes.html", usuario=usuario, ventas=ventas, gastos=gastos, compras=compras)

# ==================== RECUPERACIÓN DE CONTRASEÑA ====================

@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        correo = request.form["correo"]
        cursor.execute("SELECT id, nombre FROM usuarios WHERE correo=%s", (correo,))
        u = cursor.fetchone()
        if u:
            token = secrets.token_urlsafe(32)
            cursor.execute("INSERT INTO recuperacion (usuario_id, token) VALUES (%s, %s)", (u[0], token))
            conexion.commit()
            registrar_actividad(u[0], u[1], "Solicitud recuperación", f"Token generado para {correo}")
        return render_template("recuperar.html", enviado=True)
    return render_template("recuperar.html")

@app.route("/restablecer/<token>", methods=["GET", "POST"])
def restablecer(token):
    cursor.execute("SELECT usuario_id FROM recuperacion WHERE token=%s AND usado=FALSE AND fecha_solicitud >= DATE_SUB(NOW(), INTERVAL 1 HOUR)", (token,))
    r = cursor.fetchone()
    if not r:
        return "Token inválido o expirado"
    if request.method == "POST":
        password = request.form["password"]
        confirmar = request.form["confirmar"]
        if password != confirmar:
            return "Las contraseñas no coinciden"
        hash_pass = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("UPDATE usuarios SET password=%s WHERE id=%s", (hash_pass, r[0]))
        cursor.execute("UPDATE recuperacion SET usado=TRUE, fecha_uso=NOW() WHERE token=%s", (token,))
        conexion.commit()
        return redirect("/login")
    return render_template("restablecer.html", token=token)

# ==================== PERFIL - SUBIR FOTO ====================

@app.route("/subir_foto", methods=["POST"])
def subir_foto():
    if "usuario_id" not in session: return redirect("/login")
    if 'foto' not in request.files: return redirect("/perfil")
    file = request.files['foto']
    if file.filename == '': return redirect("/perfil")
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    filename = f"user_{session['usuario_id']}_{secrets.token_hex(4)}.{ext}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    cursor.execute("UPDATE usuarios SET foto=%s WHERE id=%s", (filename, session["usuario_id"]))
    conexion.commit()
    return redirect("/perfil")

# ==================== ACTUALIZAR PERFIL ====================

@app.route("/actualizar_perfil", methods=["POST"])
def actualizar_perfil():
    if "usuario_id" not in session: return redirect("/login")
    cursor.execute("UPDATE usuarios SET nombre=%s, apellido=%s WHERE id=%s",
                   (request.form["nombre"], request.form["apellido"], session["usuario_id"]))
    conexion.commit()
    session["usuario_nombre"] = request.form["nombre"]
    return redirect("/perfil")

if __name__ == "__main__":
    app.run(debug=True)
