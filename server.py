import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuración de la base de datos local (Persistente)
DB_NAME = "chat_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabla de mensajes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emisor TEXT NOT NULL,
            receptor TEXT NOT NULL,
            contenido TEXT NOT NULL,
            tipo TEXT DEFAULT 'texto',
            eliminado INTEGER DEFAULT 0,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Tabla de estados/historias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            url_contenido TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET'])
def inicio():
    return jsonify({"status": "Servidor activo", "app": "Lisa Chat Backend"}), 200

# 1. Registrar o Enviar Mensaje
@app.route('/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
    data = request.get_json()
    emisor = data.get('emisor')
    receptor = data.get('receptor')
    contenido = data.get('contenido')
    tipo = data.get('tipo', 'texto')

    if not emisor or not receptor or not contenido:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO mensajes (emisor, receptor, contenido, tipo) VALUES (?, ?, ?, ?)',
        (emisor, receptor, contenido, tipo)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "éxito", "mensaje": "Mensaje enviado"}), 201

# 2. Obtener Mensajes (Incluye marcados como eliminados con bandera 'eliminado = 1')
@app.route('/obtener_mensajes', methods=['GET'])
def obtener_mensajes():
    emisor = request.args.get('emisor')
    receptor = request.args.get('receptor')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, emisor, receptor, contenido, tipo, eliminado, fecha 
        FROM mensajes 
        WHERE (emisor = ? AND receptor = ?) OR (emisor = ? AND receptor = ?)
        ORDER BY fecha ASC
    ''', (emisor, receptor, receptor, emisor))
    
    filas = cursor.fetchall()
    conn.close()

    resultado = []
    for f in filas:
        resultado.append({
            "id": f[0],
            "emisor": f[1],
            "receptor": f[2],
            "contenido": f[3],
            "tipo": f[4],
            "fue_eliminado": bool(f[5]),
            "fecha": f[6]
        })

    return jsonify({"mensajes": resultado}), 200

# 3. Marcar mensaje como eliminado (No borra el registro de la DB, solo cambia el estado)
@app.route('/marcar_eliminado', methods=['POST'])
def marcar_eliminado():
    data = request.get_json()
    mensaje_id = data.get('id')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE mensajes SET eliminado = 1 WHERE id = ?', (mensaje_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "éxito", "mensaje": "Mensaje marcado como eliminado"}), 200

# 4. Publicar Estado
@app.route('/publicar_estado', methods=['POST'])
def publicar_estado():
    data = request.get_json()
    usuario = data.get('usuario')
    url_contenido = data.get('url_contenido')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO estados (usuario, url_contenido) VALUES (?, ?)', (usuario, url_contenido))
    conn.commit()
    conn.close()

    return jsonify({"status": "éxito", "mensaje": "Estado publicado"}), 201

# 5. Obtener Estados
@app.route('/obtener_estados', methods=['GET'])
def obtener_estados():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, usuario, url_contenido, fecha FROM estados ORDER BY fecha DESC')
    filas = cursor.fetchall()
    conn.close()

    estados = [{"id": f[0], "usuario": f[1], "url_contenido": f[2], "fecha": f[3]} for f in filas]
    return jsonify({"estados": estados}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
  
