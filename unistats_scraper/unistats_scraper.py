import requests
from bs4 import BeautifulSoup
from itertools import product
import sqlite3
from pathlib import Path
from datetime import datetime
import locale
import re
from time import sleep

BASE_DATOS = 'unistats_db.db'
FICHERO_DEBUG = Path('debug/debug_' + (datetime.now()).strftime('%d_%m_%Y_%H_%M_%S') + '.txt')

def inicializar_base_de_datos():
    db = sqlite3.connect(BASE_DATOS)
    cursor = db.cursor()

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS usuario (
            usuario TEXT PRIMARY KEY,
            rango TEXT,
            premium INTEGER CHECK(premium IN (0, 1)),
            fecha_ingreso DATE NULL,
            fecha_ultima DATE NULL
        )
        '''
    )
    cursor.close()
    return db

def generar_usuarios(usuario_inicial=None):
    if not usuario_inicial:
        longitud_minima = 3
        usuario_inicial = ''
    else:
        longitud_minima = len(usuario_inicial)
    longitud_maxima = 16
    charset = 'abcdefghijklmnopqrstuvwxyz_-'
    for longitud in range(longitud_minima, longitud_maxima + 1):
        for s in product(charset, repeat=longitud):
            yield usuario_inicial + ''.join(s)

def mandar_request(nick: str)
    url = "https://stats.universocraft.com/jugador/" + nick
    headers = {
        'User-Agent': 'FxrchusBbsita'
    }
    session = requests.Session()
    session.headers.update(headers)
    try:
        respuesta = session.get(url)
        respuesta.raise_for_status() # Errores HTTP
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return False
    
    

def scraper(nick: str) -> dict:
    if respuesta.url != url:
        print("Error")
        return

    pagina = BeautifulSoup(respuesta.content, 'html.parser')

    tag_nick = pagina.find('div', class_="ProfileName")
    tag_nick = tag_nick.find('h1')

    datos = {
        "usuario": tag_nick.text
    }

    tag_premium = pagina.find('span', class_="ProfileTag TagPremium")
    if tag_premium:
        datos["premium"] = 1
    else:
        datos["premium"] = 0
    tag_rango = pagina.find('span', class_="ProfileTag TagRank")
    datos["rango"] = tag_rango.text.replace('\n', '')

    tag_fecha_ultima = pagina.find('pre', class_="ProfileMainStat__Value")
    fecha_ultima = tag_fecha_ultima.text
    if fecha_ultima == '...':
        fecha_ultima = None
    else:
        fecha_ultima = fecha_ultima.split()
        fecha_ultima = datetime.strptime(fecha_ultima[0] + fecha_ultima[2] + fecha_ultima[4], "%d%B%Y")
    
    datos["fecha_ultima"] = fecha_ultima

    fecha_ingreso = None
    tags_profile_stats = pagina.find_all('div', class_="ProfileStat")
    for div in tags_profile_stats:
        name = div.find('p', class_="ProfileStat__Name")
        if name.text == "Primera Conexión":
            value = div.find('p', class_="ProfileStat__Value")
            fecha_ingreso = value.text
            fecha_ingreso = fecha_ingreso.split()
            fecha_ingreso = datetime.strptime(fecha_ingreso[0] + fecha_ingreso[2] + fecha_ingreso[4], "%d%B%Y")

    datos["fecha_ingreso"] = fecha_ingreso

    return datos
    

if __name__ == '__main__':
    locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
    db = inicializar_base_de_datos()
    for usuario in generar_usuarios():
        sleep(2)
        r = scraper(usuario)
        if r:
            print(usuario)
