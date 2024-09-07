import sqlite3
from colorama import Fore, Style
from time import sleep


BASE_DE_DATOS_SQL = './base_v3.db'
TEXTO_DE_RANGOS = 'skywars.txt'

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

db = sqlite3.connect(BASE_DE_DATOS_SQL)
cursor = db.cursor()

query = '''
    SELECT usuario
    FROM usuarios 
    NATURAL JOIN tops
    WHERE rango IS NOT NULL 
      AND rango NOT IN ('L/NE', 'NO_ENCONTRADO') 
      AND premium NOT IN ('N/LE', 'NO_ENCONTRADO', 'SI')
      AND modalidad == 'skywars'
    ORDER BY seccion, rank
'''

cursor = query_con_handling(cursor, query, ())

filas = cursor.fetchall()

usuarios = set()

for i in filas:
    usuarios.add(i[0])


lista_ingestada = []

for i in usuarios:
        query = '''
            SELECT usuario, rango, seccion, rank, valor 
            FROM usuarios 
            NATURAL JOIN tops
            WHERE rango IS NOT NULL 
            AND rango NOT IN ('L/NE', 'NO_ENCONTRADO') 
            AND premium NOT IN ('N/LE', 'NO_ENCONTRADO', 'SI')
            AND modalidad == 'skywars'
            AND usuario == ?
            ORDER BY seccion
        '''

        cursor = query_con_handling(db.cursor(), query, (i,))

        filas = cursor.fetchall()

        if len(filas) == 1:
            usuario = filas[0][0]
            rango = filas[0][1]
            seccion = filas[0][2]
            rank = filas[0][3]
            valor = filas[0][4]
        else:
            usuario = i
            rango = filas[0][1]
            seccion = "kills|wins"
            rank = (filas[0][3] + filas[1][3])/2
            if rank.is_integer():
                rank = int(rank)
            valor = str(filas[0][4]) + " | " + str(filas[1][4])
        lista_ingestada.append((usuario, rango, seccion, rank, valor))

lista_ingestada.sort(key=lambda x: x[3])


with open(TEXTO_DE_RANGOS, 'w') as archivo:
    for i in lista_ingestada:
        usuario = i[0]
        rango = i[1]
        seccion = i[2]
        rank = i[3]
        valor = i[4]
        escritura = "{:<16} {:<6} {:<12} {:<5} {:<16}\n".format(usuario, rango, seccion, rank, valor)
        archivo.write(escritura)

db.close()
