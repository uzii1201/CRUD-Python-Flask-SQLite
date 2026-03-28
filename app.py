from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import threading

app = Flask(__name__)

#---------------SQLite---------------
db_lock = threading.Lock()

def get_db():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


#---------------Clientes---------------
@app.route("/clientes")
def clientes():
    with db_lock:
        conn = get_db()
        clientes = conn.execute("SELECT * FROM clientes").fetchall()
        conn.close()
    return render_template("clientes.html", clientes=clientes)

@app.route("/clientes/crear", methods=["POST"])
def crear_cliente():
    nombre = request.form["nombre"]
    email = request.form["email"]
    with db_lock:
        conn = get_db()
        conn.execute("INSERT INTO clientes (nombre,email) VALUES (?,?)",(nombre,email))
        conn.commit()
        conn.close()
    return redirect("/clientes")

@app.route("/clientes/editar/<int:id>", methods=["GET","POST"])
def editar_cliente(id):
    with db_lock:
        conn = get_db()
        if request.method == "POST":
            nombre = request.form["nombre"]
            email = request.form["email"]
            conn.execute("UPDATE clientes SET nombre=?, email=? WHERE id=?",(nombre,email,id))
            conn.commit()
            conn.close()
            return redirect("/clientes")
        cliente = conn.execute("SELECT * FROM clientes WHERE id=?",(id,)).fetchone()
        conn.close()
    return render_template("editar_cliente.html", cliente=cliente)

@app.route("/clientes/eliminar/<int:id>")
def eliminar_cliente(id):
    with db_lock:
        conn = get_db()
        conn.execute("DELETE FROM clientes WHERE id=?",(id,))
        conn.commit()
        conn.close()
    return redirect("/clientes")

#---------------Productos---------------
@app.route("/productos")
def productos():
    with db_lock:
        conn = get_db()
        productos = conn.execute("SELECT * FROM productos").fetchall()
        conn.close()
    return render_template("productos.html", productos=productos)

@app.route("/productos/crear", methods=["POST"])
def crear_producto():
    nombre = request.form["nombre"]
    precio = float(request.form["precio"])
    stock = int(request.form["stock"])
    with db_lock:
        conn = get_db()
        conn.execute("INSERT INTO productos (nombre,precio,stock) VALUES (?,?,?)",(nombre,precio,stock))
        conn.commit()
        conn.close()
    return redirect("/productos")

@app.route("/productos/editar/<int:id>", methods=["GET","POST"])
def editar_producto(id):
    with db_lock:
        conn = get_db()
        if request.method == "POST":
            nombre = request.form["nombre"]
            precio = float(request.form["precio"])
            stock = int(request.form["stock"])
            conn.execute("UPDATE productos SET nombre=?, precio=?, stock=? WHERE id=?",(nombre,precio,stock,id))
            conn.commit()
            conn.close()
            return redirect("/productos")
        producto = conn.execute("SELECT * FROM productos WHERE id=?",(id,)).fetchone()
        conn.close()
    return render_template("editar_producto.html", producto=producto)

@app.route("/productos/eliminar/<int:id>")
def eliminar_producto(id):
    with db_lock:
        conn = get_db()
        conn.execute("DELETE FROM productos WHERE id=?",(id,))
        conn.commit()
        conn.close()
    return redirect("/productos")

# ---------------Pedidos---------------
@app.route("/pedidos")
def pedidos():
    with db_lock:
        conn = get_db()
        pedidos = conn.execute("""
            SELECT pedidos.id, clientes.nombre AS cliente, productos.nombre AS producto,
                   pedidos_productos.cantidad, productos.precio, pedidos.fecha
            FROM pedidos
            JOIN clientes ON pedidos.cliente_id = clientes.id
            JOIN pedidos_productos ON pedidos.id = pedidos_productos.pedido_id
            JOIN productos ON pedidos_productos.producto_id = productos.id
        """).fetchall()
        clientes = conn.execute("SELECT * FROM clientes").fetchall()
        productos = conn.execute("SELECT * FROM productos").fetchall()
        conn.close()
    return render_template("pedidos.html", pedidos=pedidos, clientes=clientes, productos=productos)

@app.route("/pedidos/crear", methods=["POST"])
def crear_pedido():
    cliente_id = request.form["cliente_id"]
    producto_id = request.form["producto_id"]
    cantidad = int(request.form["cantidad"])
    fecha = request.form["fecha"]

    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        return "Fecha inválida"

    with db_lock:
        conn = get_db()
        cursor = conn.cursor()

        producto = conn.execute("SELECT stock, precio FROM productos WHERE id=?",(producto_id,)).fetchone()
        if cantidad > producto["stock"]:
            conn.close()
            return f"Stock insuficiente. Disponible: {producto['stock']}"

        cursor.execute("INSERT INTO pedidos (cliente_id,fecha) VALUES (?,?)",(cliente_id,fecha))
        pedido_id = cursor.lastrowid
        cursor.execute("INSERT INTO pedidos_productos (pedido_id,producto_id,cantidad) VALUES (?,?,?)",(pedido_id,producto_id,cantidad))
        cursor.execute("UPDATE productos SET stock = stock - ? WHERE id=?",(cantidad,producto_id))

        conn.commit()
        conn.close()
    return redirect("/pedidos")

@app.route("/pedidos/editar/<int:id>", methods=["GET","POST"])
def editar_pedido(id):
    with db_lock:
        conn = get_db()
        if request.method == "POST":
            cliente_id = request.form["cliente_id"]
            producto_id = request.form["producto_id"]
            cantidad = int(request.form["cantidad"])
            fecha = request.form["fecha"]

            try:
                datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                return "Fecha inválida"

            anterior = conn.execute("SELECT producto_id,cantidad FROM pedidos_productos WHERE pedido_id=?",(id,)).fetchone()
            stock_disponible = conn.execute("SELECT stock FROM productos WHERE id=?",(producto_id,)).fetchone()["stock"] + anterior["cantidad"]

            if cantidad > stock_disponible:
                conn.close()
                return "Stock insuficiente"

            conn.execute("UPDATE productos SET stock = stock + ? WHERE id=?",(anterior["cantidad"], anterior["producto_id"]))
            conn.execute("UPDATE productos SET stock = stock - ? WHERE id=?",(cantidad, producto_id))

            conn.execute("UPDATE pedidos SET cliente_id=?, fecha=? WHERE id=?",(cliente_id, fecha, id))
            conn.execute("UPDATE pedidos_productos SET producto_id=?, cantidad=? WHERE pedido_id=?",(producto_id,cantidad,id))

            conn.commit()
            conn.close()
            return redirect("/pedidos")

        pedido = conn.execute("""
            SELECT pedidos.id, pedidos.fecha, pedidos.cliente_id,
                   pedidos_productos.producto_id, pedidos_productos.cantidad
            FROM pedidos
            JOIN pedidos_productos ON pedidos.id = pedidos_productos.pedido_id
            WHERE pedidos.id=?
        """,(id,)).fetchone()
        clientes = conn.execute("SELECT * FROM clientes").fetchall()
        productos = conn.execute("SELECT * FROM productos").fetchall()
        conn.close()
    return render_template("editar_pedido.html", pedido=pedido, clientes=clientes, productos=productos)

@app.route("/pedidos/eliminar/<int:id>")
def eliminar_pedido(id):
    with db_lock:
        conn = get_db()
        item = conn.execute("SELECT producto_id,cantidad FROM pedidos_productos WHERE pedido_id=?",(id,)).fetchone()
        conn.execute("UPDATE productos SET stock = stock + ? WHERE id=?",(item["cantidad"], item["producto_id"]))
        conn.execute("DELETE FROM pedidos_productos WHERE pedido_id=?",(id,))
        conn.execute("DELETE FROM pedidos WHERE id=?",(id,))
        conn.commit()
        conn.close()
    return redirect("/pedidos")


#---------------main---------------

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)