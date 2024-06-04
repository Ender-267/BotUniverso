import sqlite3
from datetime import datetime

BASE_DE_DATOS_SQL = './base.db'
TEXTO_DE_FECHA = './fecha.txt'
TEXTO_DE_RANGOS = './rangos_' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.txt'

with open(TEXTO_DE_FECHA, 'r') as archivo:
    fecha = archivo.read()

db = sqlite3.connect(BASE_DE_DATOS_SQL)
cursor = db.cursor()

cursor.execute("SELECT usuario, rango, ip, contra FROM usuarios NATURAL JOIN datos WHERE rango IS NOT NULL AND rango != 'USU' AND rango != 'L/NE' AND rango != 'NO_ENCONTRADO' AND premium != 'N/LE' AND premium != 'NO_ENCONTRADO' AND fecha_lectura > datetime(?, '-1 minute') ORDER BY usuario", (fecha,))

with open(TEXTO_DE_FECHA, 'w') as archivo:
    s = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    archivo.write(s)

filas = cursor.fetchall()
with open(TEXTO_DE_RANGOS, 'w') as archivo:
    for fila in filas:
        usuario = fila[0]
        rango = fila[1]
        ip = fila[2]
        contra = fila[3]
        if not ip:
            ip = 'NO_HAY_IP'
        escritura = "{:<16} {:<6} {:<16} {:<16}\n".format(usuario, rango, ip, contra)
        archivo.write(escritura)