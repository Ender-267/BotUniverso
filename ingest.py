import sqlite3
from pathlib import Path
import json
import pandas as pd

BASE_DE_DATOS_SQL = './base.db'
TXT_HYCRAFT = './hycraft.txt'
TXT_RANGOS = './rangos.txt'
TXT_OMEGACRAFT = './OmegaCraft.json'
TXT_LISTA_LEIDOS = './n2_hycraft.txt'


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

def insertar_lista_leidos():
    with open(TXT_LISTA_LEIDOS, 'r', encoding='utf-8') as archivo:
        datos = archivo.readlines()
    db = sqlite3.connect(BASE_DE_DATOS_SQL)
    cur = db.cursor()
    for linea in datos:
        linea = linea.strip().split()
        usuario = linea[0]
        premium = 'L/NE'
        rango = 'L/NE'
        date = '2020-01-01'
        querry = '''UPDATE usuarios SET rango=?, fecha_lectura=?, premium=? WHERE usuario=?'''
        cur.execute(querry, (rango, date, premium, usuario))
    db.commit()
    db.close()



def insertar_rangos():
    with open(TXT_RANGOS, 'r') as archivo:
        datos = archivo.readlines()
    db = sqlite3.connect(BASE_DE_DATOS_SQL)
    cur = db.cursor()
    for linea in datos:
        d = linea.strip().replace('\n', '').split()
        usuario = d[0].lower()
        rango = d[2]
        date = '2020-01-01'
        premium = 'NO'
        querry = '''UPDATE usuarios SET rango=?, fecha_lectura=?, premium=? WHERE usuario=?'''
        cur.execute(querry, (rango, date, premium, usuario))
    db.commit()
    db.close()


def ingestas_omegacraft():
    with open(TXT_OMEGACRAFT, 'r') as file:
        datos = json.load(file)

    usuarios_unicos = {}
    for usuario in datos:
        nombre = usuario['name'].lower()
        contra = usuario['password']
        if nombre in usuarios_unicos:
            usuarios_unicos[nombre].append(contra)
        else:
            usuarios_unicos[nombre] = [contra]
    db = sqlite3.connect(BASE_DE_DATOS_SQL)
    cur = db.cursor()
    for usuario, contras in usuarios_unicos.items():
        datos = []
        for contra in contras:
            datos.append((contra, None))
        obj = Usuario(usuario, datos)
        obj.insertar_a_db(cur)
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
            tipo_contra TEXT NOT NULL,
            FOREIGN KEY (usuario) REFERENCES usuarios(usuario)
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_rango ON usuarios(rango)')

    db.commit()
    db.close()

if __name__ == '__main__':
    crear_db()
    ingestar_hycraft()
    ingestas_omegacraft()
    insertar_rangos()
    insertar_lista_leidos()

        