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
        "Accept-Encoding": "gzip, deflate, zstd",
        "Accept-Language": "es-ES,es;q=0.5",
        "Cache-Control": "max-age=0",
        "Cookie": token,
        "Priority": "u=0, i",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Brave";v="126"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Model": '""',
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Ch-Ua-Platform-Version": '"15.0.0"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Sec-Gpc": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    session = requests.Session()
    session.headers.update(headers)
    try:
        respuesta = session.get(url)
        if respuesta.status_code == 403:
            print(Fore.YELLOW + "Error 403 Forbidden" + Style.RESET_ALL)
            token = None
            while not token:
                sleep(2)
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

def scraper():
    try:
        with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
            cursor = db.cursor()
            querry = "SELECT usuario FROM usuarios WHERE rango IS NULL ORDER BY RANDOM() LIMIT 1"
            while True:
                cursor.execute(querry)
                usuario = cursor.fetchone()[0]
                if not usuario:
                    print(Fore.YELLOW + "La querry SQL no retorno ningun usuario"+ Style.RESET_ALL)
                    return
                sleep(1.2)
                ret = unistats(usuario)
                if ret == 'ERROR':
                    continue
                rango = ret[0]
                premium = ret[1]
                fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if not premium and not rango:
                    cursor.execute("UPDATE usuarios SET rango=?, premium=?, fecha_lectura=? WHERE usuario=?", ('NO_ENCONTRADO', 'NO_ENCONTRADO', fecha, usuario))
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
                cursor.execute("UPDATE usuarios SET rango=?, premium=?, fecha_lectura=? WHERE usuario=?", (rango, premium, fecha, usuario))
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
    obtener_token()
    scraper()