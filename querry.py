import sqlite3
from datetime import datetime
from colorama import Fore, Style
from time import sleep


BASE_DE_DATOS_SQL = './base.db'
TEXTO_DE_FECHA = './fecha.txt'
TEXTO_DE_RANGOS = './rangos_' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.txt'

def query_con_handling(cur: sqlite3.Cursor, query: str, tupla: tuple = ()):
    try:
        cur.execute(query, tupla)
        cur.connection.commit()
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print(f"{Fore.YELLOW}Base de datos bloqueada{Style.RESET_ALL}")
            sleep(2)
            return query_con_handling(cur, query, tupla)
        else:
            raise
    return cur

with open(TEXTO_DE_FECHA, 'r') as archivo:
    fecha = archivo.read()

db = sqlite3.connect(BASE_DE_DATOS_SQL)
cursor = db.cursor()

querry = '''
SELECT usuario, rango, ip, contra 
    FROM usuarios 
    NATURAL JOIN datos 
    WHERE rango IS NOT NULL 
      AND rango NOT IN ('USU', 'L/NE', 'NO_ENCONTRADO') 
      AND premium NOT IN ('N/LE', 'NO_ENCONTRADO', 'SI') 
      AND fecha_lectura > datetime(?, '-1 minute') 
    ORDER BY usuario
'''
tupla = (fecha,)

cursor = query_con_handling(cursor, querry, tupla)

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

db.close()