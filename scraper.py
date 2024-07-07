from bs4 import BeautifulSoup
from time import sleep
import sqlite3
from datetime import datetime
from colorama import Fore, Style
import requests
from sys import argv
import json

BASE_DE_DATOS_SQL = './base_v3.db'
TOKEN_TXT = './token.json'
    
def obtener_token():
    global token
    global header_id
    with open(TOKEN_TXT, 'r', encoding='utf-8') as archivo:
        datos = json.load(archivo)
        if datos["token"] != token:
            token = datos["token"]
            header_id = datos["header_id"]
            return
    with open(TOKEN_TXT, 'w', encoding='utf-8') as archivo:
        datos["http_error"] = True
        json.dump(datos, archivo)
    while datos["http_error"]:
        sleep(5)
        with open(TOKEN_TXT, 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)
            print(Fore.CYAN + "Lectura de token..." + Style.RESET_ALL)
            token = datos["token"]
            header_id = datos["header_id"]

def convert_date(fecha_str):
    if '...' in fecha_str:
        return '...'
    fecha_str = fecha_str.replace('\n', ' - ')

    fecha, hora = fecha_str.split(' - ')
    
    dia_mes, año = fecha.split(' del ')
    dia, mes = dia_mes.split(' de ')
    
    meses_españoles = {
        'Enero': '01',
        'Febrero': '02',
        'Marzo': '03',
        'Abril': '04',
        'Mayo': '05',
        'Junio': '06',
        'Julio': '07',
        'Agosto': '08',
        'Septiembre': '09',
        'Octubre': '10',
        'Noviembre': '11',
        'Diciembre': '12'
    }

    mes = meses_españoles[mes]
    
    hora = hora.replace('.', '').split(' ')
    hora = hora[0] + ' ' + hora[1]
    if hora.startswith('00'):
        hora = '12' + hora[2:]
    time_obj = datetime.strptime(hora, '%I:%M %p')
    time_24hr = time_obj.strftime('%H:%M:%S')
    
    fecha_final = f'{año}-{mes}-{dia} {time_24hr}'
    
    return fecha_final


def unistats(nick: str):
    global token
    global header_id
    headers = (
        {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8",
        "Accept-Encoding": "gzip, deflate, zstd",
        "Accept-Language": "es-ES,es;q=0.6",
        "Cache-Control": "max-age=0",
        "Origin": "https://stats.universocraft.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    },
    {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, zstd",
        "Accept-Language": "es-ES,es;q=0.6",
        "Cache-Control": "max-age=0",
        "Origin": "https://stats.universocraft.com",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    },
    {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8",
        "Accept-Encoding": "gzip, deflate, zstd",
        "Accept-Language": "es-ES,es;q=0.6",
        "Cache-Control": "max-age=0",
        "Origin": "https://stats.universocraft.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    )
    url = "https://stats.universocraft.com/jugador/" + nick
    header = headers[header_id]
    header["Cookie"] = "cf_clearance=" + token


    session = requests.Session()
    session.headers.update(header)
    try:
        respuesta = session.get(url)
        if respuesta.status_code == 403:
            print(Fore.YELLOW + "Error 403 Forbidden" + Style.RESET_ALL)
            obtener_token()
            return unistats(nick)
        elif respuesta.status_code == 404:
            print(Fore.RED + "Error 404 Not Found" + Style.RESET_ALL)
            sleep(8)
            return unistats(nick)
        respuesta.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return 'ERROR'

    url_error = "https://stats.universocraft.com/?error=true"
    if respuesta.url == url_error:
        return 'NO ENCONTRADO'

    pagina = BeautifulSoup(respuesta.text, 'html.parser')

    tag_premium = pagina.find('span', class_="ProfileTag TagPremium")
    if tag_premium:
        premium = 'SI'
    else:
        premium = 'NO'

    tag_rango = pagina.find('span', class_="ProfileTag TagRank")
    if not tag_rango:
        print(Fore.YELLOW + "Error de carga de pagina desconocido" + Style.RESET_ALL)
        sleep(2)
        return unistats(nick)
    rango = tag_rango.text.replace('\n', '').replace(' ', '')

    tag_fecha_last = pagina.find('pre', class_="ProfileMainStat__Value")
    fecha_last = tag_fecha_last.text
    fecha_last = convert_date(fecha_last)

    tag_fecha_prim = pagina.find_all('p', class_="ProfileStat__Value")
    if len(tag_fecha_prim) == 3:
        tag_fecha_prim = tag_fecha_prim[1]
        fecha_prim = convert_date(tag_fecha_prim.text)
    else:
        fecha_prim = '...'

    ret_dict = {
        'rango': rango,
        'premium': premium,
        'fecha_last': fecha_last,
        'fecha_prim': fecha_prim
    }
    return ret_dict


def texto_rango(rango: str) -> str | None:
    if not rango:
        return None
    rango = rango[:3]
    match rango:
        case 'USU':
            texto_rango = '{}{}{}'.format(Fore.WHITE, rango, Style.RESET_ALL)
        case 'JUP':
            texto_rango = '{}{}{}'.format(Fore.CYAN, rango, Style.RESET_ALL)
        case 'NEP':
            texto_rango = '{}{}{}'.format(Fore.BLUE, rango, Style.RESET_ALL)
        case 'MER':
            texto_rango = '{}{}{}'.format(Fore.GREEN, rango, Style.RESET_ALL)
        case 'SAT':
            texto_rango = '{}{}{}'.format(Fore.MAGENTA, rango, Style.RESET_ALL)
        case 'AYU':
            texto_rango = '{}{}{}'.format(Fore.YELLOW, rango, Style.RESET_ALL)
        case 'MOD':
            texto_rango = '{}{}{}'.format(Fore.CYAN, rango, Style.RESET_ALL)
        case 'ADM':
            texto_rango = '{}{}{}'.format(Fore.RED, rango, Style.RESET_ALL)
        case 'YT':
            texto_rango = '{}{}{}'.format(Fore.RED, rango, Style.RESET_ALL)
        case 'STR':
            texto_rango = '{}{}{}'.format(Fore.MAGENTA, rango, Style.RESET_ALL)
        case _:
            texto_rango = f"NR{rango}"
    return texto_rango

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

def generar_queue():
    try:
        with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
            cursor = db.cursor()
            querry =  '''SELECT DISTINCT u.*
                FROM usuarios u
                JOIN datos d ON u.usuario = d.usuario
                WHERE d.db_proveniente IN ('OMEGACRAFT', 'HYCRAFT')
                ORDER BY RANDOM()
                LIMIT 10000
                '''
            cursor = query_con_handling(cursor, querry)
            queue = cursor.fetchall()
            print(Fore.CYAN + "Queue regenerada" + Style.RESET_ALL)
            return queue
    except Exception as e:
        print(e)
        sleep(3)
        db.commit()
        db.close()
        return

def scraper():
    queue = generar_queue()
    try:
        with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
            cursor = db.cursor()
            while True:
                if len(queue) == 0:
                    queue = generar_queue()
                    if len(queue) == 0:
                        print(Fore.YELLOW + "La querry SQL no retorno ningun usuario"+ Style.RESET_ALL)
                        return
                usuario = queue.pop()[0]
                if usuario is None:
                    continue
                sleep(1.2)
                ret = unistats(usuario)
                if ret == 'ERROR':
                    continue
                fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if ret == 'NO ENCONTRADO':
                    query = "UPDATE usuarios SET rango=?, premium=?, fecha_lectura=? WHERE usuario=?"
                    tupla = ('NO_ENCONTRADO', 'NO_ENCONTRADO', fecha, usuario)
                    cursor = query_con_handling(cursor, query, tupla)
                    print("{:<16} {}NO ENCONTRADO{}".format(usuario, Fore.RED, Style.RESET_ALL))
                    continue
                rango = ret['rango']
                premium = ret['premium']
                fecha_prim = ret['fecha_prim']
                fecha_last = ret['fecha_last']
                  
                match premium:
                    case 'SI':
                        texto_premium = "PREMIUM"
                    case 'NO':
                        texto_premium = "NO_PREMIUM"
                    case _:
                        texto_premium = "WTF"
                query = """
                    UPDATE usuarios 
                    SET rango=?, premium=?, fecha_lectura=?, fecha_ultima_con=?, fecha_primer_login=? 
                    WHERE usuario=?
                """
                tupla = (rango, premium, fecha, fecha_last, fecha_prim, usuario)
                cursor = query_con_handling(cursor, query, tupla)
                s = "{:<16} {:<8} {:<8}\n".format(usuario, texto_rango(rango), texto_premium)
                print(s, end='')
    except Exception as e:
        print(e)
        sleep(3)
        db.commit()
        db.close()
        return



if __name__ == '__main__':
    token = None
    obtener_token()
    scraper()