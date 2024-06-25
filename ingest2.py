import sqlite3

def crear_db_nueva():
    with sqlite3.connect('neobase.db') as db:
        cur = db.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario TEXT PRIMARY KEY,
                rango TEXT,
                fecha_ultima_con DATE,
                fecha_primer_login DATE,
                fecha_lectura DATE,
                premium TEXT,
                CONSTRAINT check_dates CHECK (rango IS NULL OR fecha_lectura IS NOT NULL)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS datos (
                id INTEGER PRIMARY KEY,
                usuario TEXT NOT NULL,
                contra TEXT NOT NULL,
                ip TEXT,
                tipo_contra INTEGER NOT NULL,
                FOREIGN KEY (usuario) REFERENCES usuarios(usuario)
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS plots (
                coordenada_x INTEGER,
                coordenada_y INTEGER,
                dueño TEXT NOT NULL,
                PRIMARY KEY (coordenada_x, coordenada_y),
                FOREIGN KEY (dueño) REFERENCES usuarios(usuario)
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS pertenece_a_plot (
                id INTEGER PRIMARY KEY,
                coordenada_x INTEGER NOT NULL,
                coordenada_y INTEGER NOT NULL,
                usuario TEXT NOT NULL,
                tipo_relacion TEXT NOT NULL,
                FOREIGN KEY (coordenada_x) REFERENCES plots(coordenada_x),
                FOREIGN KEY (coordenada_y) REFERENCES plots(coordenada_y),
                FOREIGN KEY (usuario) REFERENCES usuarios(usuario)
            )
        ''')
        db.commit()

def migrar_datos():
    con_fuente = sqlite3.connect('base.db')
    con_objetivo = sqlite3.connect('neobase.db')

    try:
        cur_fuente = con_fuente.cursor()
        cur_objetivo = con_objetivo.cursor()

        cur_fuente.execute("SELECT usuario, rango, fecha_lectura, premium FROM usuarios")
        usuarios = cur_fuente.fetchall()

        datos_usuarios = []
        for usuario in usuarios:
            nick = usuario[0]
            rango = usuario[1]
            fecha_lectura = usuario[2]
            premium = usuario[3]
            insertar = (nick, rango, None, None, fecha_lectura, premium)
            datos_usuarios.append(insertar)

        cur_objetivo.executemany(
            "INSERT INTO usuarios (usuario, rango, fecha_ultima_con, fecha_primer_login, fecha_lectura, premium) VALUES (?, ?, ?, ?, ?, ?)",
            datos_usuarios
        )
        
        cur_fuente.execute("SELECT id, usuario, contra, ip, tipo_contra FROM datos")
        datos = cur_fuente.fetchall()

        insert_data_datos = []
        for dato in datos:
            id, usuario, contra, ip, tipo_contra = dato
            tipo_contra = 20711 if tipo_contra == "HASH_SHA" else -1
            insert_data_datos.append((id, usuario, contra, ip, tipo_contra))

        cur_objetivo.executemany(
            "INSERT INTO datos (id, usuario, contra, ip, tipo_contra) VALUES (?, ?, ?, ?, ?)",
            insert_data_datos
        )

        con_objetivo.commit()

    except Exception as e:
        con_objetivo.rollback()
        print(f"An error occurred: {e}")

    finally:
        # Close the connections
        con_fuente.close()
        con_objetivo.close()

if __name__ == '__main__':
    crear_db_nueva()
    migrar_datos()
