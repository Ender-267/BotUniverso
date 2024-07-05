import sqlite3
import json

def crear_db_nueva():
    with sqlite3.connect('base_v3.db') as db:
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
            CREATE TABLE IF NOT EXISTS pertenece_a_db (
                id INTEGER PRIMARY KEY,
                usuario TEXT,
                db_original TEXT,
                FOREIGN KEY (usuario) REFERENCES usuarios(usuario)
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
        db.commit()

def migrar_datos():
    con_fuente = sqlite3.connect('neobase.db')
    con_objetivo = sqlite3.connect('base_v3.db')

    try:
        cur_fuente = con_fuente.cursor()
        cur_objetivo = con_objetivo.cursor()

        cur_fuente.execute("SELECT usuario, rango, fecha_ultima_con, fecha_primer_login, fecha_lectura, premium FROM usuarios")
        usuarios = cur_fuente.fetchall()

        datos_usuarios = []
        for usuario in usuarios:
            nick = usuario[0]
            rango = usuario[1]
            fecha_ultima_con = usuario[2]
            fecha_primer_login = usuario[3]
            fecha_lectura = usuario[4]
            premium = usuario[5]
            insertar = (nick, rango, fecha_ultima_con, fecha_primer_login, fecha_lectura, premium)
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

BASE_DE_DATOS_SQL = './base_v3.db'
TXT_HYCRAFT = './hycraft.txt'
TXT_OMEGACRAFT = './OmegaCraft.json'

class Usuario:
    def __init__(self, usuario: str, datos: list[tuple]):
        self.usuario = usuario
        self.datos = datos

    def insertar_a_db(self, cur: sqlite3.Cursor):
        # Insert into usuarios table
        cur.execute('''
                INSERT OR IGNORE INTO usuarios (usuario)
                VALUES (?)
            ''', (self.usuario,))
        
        for dato in self.datos:
            passw = dato[0]
            ip = dato[1]
            if passw[:5] == "$SHA$":
                tipo = "HASH_SHA"
            else:
                tipo = "TEXTO"
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra)
                VALUES (?, ?, ?, ?)
            ''', (self.usuario, passw, ip, tipo))

def ingestas_omegacraft():
    with open(TXT_OMEGACRAFT, 'r') as file:
        datos = json.load(file)

    usuarios_unicos = []
    for usuario in datos:
        if usuario not in usuarios_unicos:
            usuarios_unicos[nombre].append(contra)
        else:
            usuarios_unicos[nombre] = [contra]
    db = sqlite3.connect(BASE_DE_DATOS_SQL)
    cur = db.cursor()
    cur.executemany()
    db.commit()
    db.close()


def ingestar_hycraft():
    with open(TXT_HYCRAFT, 'r', encoding='utf-8') as archivo:
        datos = archivo.readlines()

    user_data = {}

    for linea in datos:
        if 'nick:' in linea:
            nickname = linea.split(': ')[1].strip().strip('"').lower()
            user_data.setdefault(nickname, [])
        elif 'password:' in linea:
            password = linea.split(': ')[1].strip().strip('"')
            user_data[nickname].append((password, None))
        elif 'ip:' in linea:
            ip = linea.split(': ')[1].strip().strip('"')
            user_data[nickname][-1] = (user_data[nickname][-1][0], ip)

    lista_ingestada = [Usuario(nick, data) for nick, data in user_data.items()]

    db = sqlite3.connect(BASE_DE_DATOS_SQL)
    cur = db.cursor()
    for i in lista_ingestada:
        i: Usuario
        i.insertar_a_db(cur)
    db.commit()
    db.close()

if __name__ == '__main__':
    crear_db_nueva()
    migrar_datos()
