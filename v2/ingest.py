import sqlite3
from pathlib import Path

BASE_DE_DATOS_SQL = './v2/base.db'
TXT_HYCRAFT = './v2/hycraft.txt'

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
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip)
                VALUES (?, ?, ?)
            ''', (self.usuario, passw, ip))


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


def crear_db():
    db = sqlite3.connect(BASE_DE_DATOS_SQL)
    cur = db.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            rango TEXT,
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
            FOREIGN KEY (usuario) REFERENCES usuarios(usuario)
        )
    ''')

    db.commit()
    db.close()

if __name__ == '__main__':
    crear_db()
    ingestar_hycraft()