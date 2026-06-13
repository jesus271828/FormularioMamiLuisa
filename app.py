from flask import Flask, render_template, request, send_file, redirect, url_for, session
import sqlite3
import csv
import io

app = Flask(__name__)
# Llave secreta para proteger las sesiones de usuario
app.secret_key = 'clave_secreta_super_segura_mami_luisa'

# CREDENCIALES POR DEFECTO
USUARIO_ADMIN = "admin"
CLAVE_ADMIN = "mamiluisa2026"

def init_db():
    conn = sqlite3.connect('colegio.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admisiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano_escolar TEXT, fecha_registro TEXT, grado_aplica TEXT,
            est_nombres TEXT, est_apellidos TEXT, est_fecha_nac TEXT, est_edad INTEGER, est_sexo TEXT,
            est_nacionalidad TEXT, est_lugar_nac TEXT, est_direccion TEXT, est_cant_hermanos INTEGER,
            est_edades_hermanos TEXT, est_lugar_ocupa TEXT, est_tipo_sangre TEXT, est_seguro_medico TEXT,
            est_alergias TEXT, est_medicamentos TEXT, est_medico_pediatra TEXT, est_centro_medico TEXT,
            est_emergencia_tel TEXT, est_emergencia_nombre TEXT, est_emergencia_parentesco TEXT,
            padre_nombre TEXT, padre_direccion TEXT, padre_sector TEXT, padre_ocupacion TEXT, padre_cedula TEXT,
            padre_nivel_acad TEXT, padre_religion TEXT, padre_telefono_pers TEXT, padre_telefono_trab TEXT, padre_correo TEXT,
            madre_nombre TEXT, madre_direccion TEXT, madre_sector TEXT, madre_ocupacion TEXT, madre_cedula TEXT,
            madre_nivel_acad TEXT, madre_religion TEXT, madre_telefono_pers TEXT, madre_telefono_trab TEXT, madre_correo TEXT,
            tutor_nombre TEXT, tutor_direccion TEXT, tutor_sector TEXT, tutor_ocupacion TEXT, tutor_cedula TEXT,
            tutor_nivel_acad TEXT, tutor_religion TEXT, tutor_telefono_pers TEXT, tutor_telefono_trab TEXT, tutor_correo TEXT
        )
    ''')
    conn.commit()
    conn.close()

# RUTA 1: CONTROL DE LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == USUARIO_ADMIN and password == CLAVE_ADMIN:
            session['usuario_logueado'] = username
            return redirect(url_for('menu_principal'))
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos")
            
    return render_template('login.html', error=None)

# RUTA 2: CERRAR SESIÓN
@app.route('/logout')
def logout():
    session.pop('usuario_logueado', None)
    return redirect(url_for('login'))

# RUTA 3: MENÚ PRINCIPAL (Protegido)
@app.route('/')
def menu_principal():
    if 'usuario_logueado' not in session:
        return redirect(url_for('login'))
    return render_template('menu.html')

# RUTA 4: FORMULARIO DE REGISTRO (Protegido)
@app.route('/registrar')
def pantalla_registro():
    if 'usuario_logueado' not in session:
        return redirect(url_for('login'))
    return render_template('formulario.html', modo="registrar", resultados=None)

# RUTA 5: BUSCADOR (Protegido)
@app.route('/buscar_pantalla')
def pantalla_buscar():
    if 'usuario_logueado' not in session:
        return redirect(url_for('login'))
    return render_template('formulario.html', modo="buscar", resultados=None)

@app.route('/guardar', methods=['POST'])
def guardar():
    if 'usuario_logueado' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        formulario_dict = request.form.to_dict()
        columnas = ', '.join(formulario_dict.keys())
        valores = tuple(formulario_dict.values())
        signos_interrogacion = ', '.join(['?'] * len(valores))
        
        try:
            conn = sqlite3.connect('colegio.db')
            cursor = conn.cursor()
            query = f"INSERT INTO admisiones ({columnas}) VALUES ({signos_interrogacion})"
            cursor.execute(query, valores)
            conn.commit()
            conn.close()
            return render_template('formulario.html', modo="registrar", mensaje="¡Ficha guardada exitosamente en la Base de Datos!")
            
        except sqlite3.OperationalError as e:
            error_msg = str(e)
            if "has no column named" in error_msg:
                nueva_columna = error_msg.split("named ")[1]
                conn = sqlite3.connect('colegio.db')
                cursor = conn.cursor()
                cursor.execute(f"ALTER TABLE admisiones ADD COLUMN {nueva_columna} TEXT")
                query = f"INSERT INTO admisiones ({columnas}) VALUES ({signos_interrogacion})"
                cursor.execute(query, valores)
                conn.commit()
                conn.close()
                return render_template('formulario.html', modo="registrar", mensaje="¡Ficha guardada! (Base de Datos actualizada automáticamente).")
            else:
                return f"Error inesperado: {e}"

@app.route('/buscar', methods=['GET'])
def buscar():
    if 'usuario_logueado' not in session:
        return redirect(url_for('login'))
        
    query_busqueda = request.args.get('query', '')
    conn = sqlite3.connect('colegio.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM admisiones 
        WHERE est_nombres LIKE ? OR est_apellidos LIKE ?
    ''', (f'%{query_busqueda}%', f'%{query_busqueda}%'))
    resultados = cursor.fetchall()
    conn.close()
    return render_template('formulario.html', modo="buscar", resultados=resultados)

@app.route('/exportar')
def exportar_excel():
    if 'usuario_logueado' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('colegio.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admisiones")
    filas = cursor.fetchall()
    columnas = [descripcion[0].upper().replace('_', ' ') for descripcion in cursor.description]
    conn.close()
    
    output = io.StringIO()
    output.write(u'\ufeff')
    writer = csv.writer(output, delimiter= ';')
    writer.writerow(columnas)
    writer.writerows(filas)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='Reporte_Admisiones_Mami_Luisa.csv'
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)