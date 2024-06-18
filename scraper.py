from bs4 import BeautifulSoup
from time import sleep
import sqlite3
from datetime import datetime
from colorama import Fore, Style
import requests
from sys import argv
import json

BASE_DE_DATOS_SQL = './base.db'
TOKEN_TXT = './token.json'
    
def obtener_token():
    global token
    with open(TOKEN_TXT, 'r', encoding='utf-8') as archivo:
        datos = json.load(archivo)
        if datos["token"] != token:
            token = datos["token"]
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

def unistats(nick: str):
    global token
    url = "https://stats.universocraft.com/jugador/" + nick
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es-ES,es;q=0.6",
        "Cookie": token,
        "Priority": "u=0, i",
        "Sec-Ch-Ua": '"Not A;Brand";v="99", "Chromium";v="125", "Google Chrome";v="125"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Model": '""',
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Ch-Ua-Platform-Version": '"10.0"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-Gpc": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }


    session = requests.Session()
    session.headers.update(headers)
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
        return (None, None)

    pagina = BeautifulSoup(respuesta.text, 'html.parser')

    tag_premium = pagina.find('span', class_="ProfileTag TagPremium")
    if tag_premium:
        premium = 'SI'
    else:
        premium = 'NO'

    tag_rango = pagina.find('span', class_="ProfileTag TagRank")
    rango = tag_rango.text.replace('\n', '').replace(' ', '')
    return (rango, premium)


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

def querry_con_handling(cur: sqlite3.Cursor,querry: str, tupla: tuple = ()):
    try:
        cur.execute(querry, tupla)
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print(f"{Fore.YELLOW}Base de datos bloqueada{Style.RESET_ALL}")
            sleep(2)
            return querry_con_handling(cur)
        else:
            raise
    return cur

def generar_queue():
    try:
        with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
            cursor = db.cursor()
            querry = "SELECT usuario FROM usuarios WHERE rango IS NULL ORDER BY RANDOM() LIMIT 10000"
            cursor = querry_con_handling(cursor, querry)
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
                sleep(1.2)
                ret = unistats(usuario)
                if ret == 'ERROR':
                    continue
                rango = ret[0]
                premium = ret[1]
                fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if not premium and not rango:
                    query = "UPDATE usuarios SET rango=?, premium=?, fecha_lectura=? WHERE usuario=?"
                    tupla = ('NO_ENCONTRADO', 'NO_ENCONTRADO', fecha, usuario)
                    cursor = querry_con_handling(cursor, query, tupla)
                    db.commit()
                    print("{:<16} {}NO ENCONTRADO{}".format(usuario, Fore.RED, Style.RESET_ALL))
                    continue
                match premium:
                    case 'SI':
                        texto_premium = "PREMIUM"
                    case 'NO':
                        texto_premium = "NO_PREMIUM"
                    case _:
                        texto_premium = "WTF"
                query = "UPDATE usuarios SET rango=?, premium=?, fecha_lectura=? WHERE usuario=?"
                tupla = (rango, premium, fecha, usuario)
                cursor = querry_con_handling(cursor, query, tupla)
                db.commit()
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