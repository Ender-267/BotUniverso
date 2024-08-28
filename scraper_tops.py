from bs4 import BeautifulSoup
from time import sleep
import sqlite3
from datetime import datetime
from colorama import Fore, Style
import requests
from sys import argv
import re

BASE_DE_DATOS_SQL = './base_v3.db'
UNISTATS_URL = 'https://stats.universocraft.com/tops/'
TOKEN = ''

def crear_tabla():
    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        query = '''
            CREATE TABLE IF NOT EXISTS tops (
                id INTEGER PRIMARY KEY,
                usuario TEXT NOT NULL,
                modalidad TEXT NOT NULL,
                seccion TEXT NOT NULL,
                valor TEXT NOT NULL,
                rank INTEGER NOT NULL,
                FOREIGN KEY (usuario) REFERENCES usuarios(usuario)
            );
        '''
        cur.execute(query)


def scraper(pagina: int , modalidad: str, seccion: str):
    url = UNISTATS_URL + modalidad + '/' + seccion + '?page=' + str(pagina)
    header = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,/;q=0.8",
        "Accept-Encoding": "gzip",
        "Accept-Language": "es-ES,es;q=0.6",
        "Cache-Control": "max-age=0",
        "Origin": "https://stats.universocraft.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Cookies": "cfclearance=" + TOKEN
    }

    session = requests.Session()
    session.headers.update(header)
    try:
        respuesta = session.get(url)
        if respuesta.status_code == 403:
            print(Fore.YELLOW + "Error 403 Forbidden" + Style.RESET_ALL)
            return
        elif respuesta.status_code == 404:
            print(Fore.RED + "Error 404 Not Found" + Style.RESET_ALL)
            sleep(8)
            return scraper(pagina, modalidad, seccion)
        respuesta.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return 'ERROR'
    
    html = BeautifulSoup(respuesta.content, 'html.parser')

    global resultados

    if pagina == 1:
        div_tops = html.find_all('div', class_= 'FirstLocale')
        for top in div_tops:
            jugador = top.find('div', class_ = 'FirstLocale__PlayerName').text.strip()
            valor = top.find('p', class_ = 'FirstLocale__Value').text.strip()
            rank = top.find('div', class_ = 'FirstLocale__Number').text.strip().replace('#', '')
            resultados.append((rank, jugador, valor))

    regex_clase_loc = re.compile(r'\bLocale\b(\s+Locale--number-\d+)?\b')

    div_tops_bajos = html.find_all('div', class_=regex_clase_loc)

    for top in div_tops_bajos:
        rank = top.find('div', class_ = 'Locale__Number').text.strip().replace('#', '')
        jugador = top.find('div', class_ = 'Locale__Description').text.strip()
        valor = top.find('div', class_ = 'Locale__Value').text.strip()
        resultados.append((rank, jugador, valor))

    return resultados


def insertar_datos_a_db(res: list, modalidad: str, seccion: str):
    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for rank, jugador, valor in res:
            jugador = jugador.lower()
            query = '''
                INSERT OR IGNORE INTO usuarios (usuario, rango, fecha_ultima_con, fecha_lectura, premium)
                VALUES (?, ?, ?, ?, ?)
            '''
            cur.execute(query, (jugador, None, None, None, None))
            query = '''
                INSERT OR IGNORE INTO tops (usuario, modalidad, seccion, valor, rank)
                VALUES (?, ?, ?, ?, ?)
            '''
            cur.execute(query, (jugador, modalidad, seccion, valor, rank))


if __name__ == '__main__':
    crear_tabla()
    modalidades = {
        'partygames': ('wins', 'kills'),
        'speedbuilders': ('wins', 'pbuilds'),
        'teamskywars': ('wins', 'kills'),
        'buildbattle': ('wins', 'points'),
        'skypit': ('kills', 'level'),
        'tntrun': ('wins',),
        'ctw': ('score', 'melee_kills', 'bow_kills', 'bow_distance_kill', 'wool_placed', 'double_wool_placed'),
        'eggwars': ('wins', 'kills', 'eggs_broken'),
        'den': ('wins', 'kills', 'damage_nexus'),
        'murdermystery': ('wins', 'kills'),
        'arenapvp': ('wins', 'kills', 'global_elo'),
        'skywars': ('wins', 'kills'),
        'uhc': ('wins', 'kills'),
        'sg': ('wins', 'kills'),
        'tnttag': ('wins', 'kills'),
        'skyblock': ('level', 'kills'),
        'bedwars': ('wins', 'kills', 'final_kills', 'beds_destroyed'),
        'edlb': ('wins', 'kills', 'rwins', 'rkills', 'bwins', 'bkills'),
        'luckywars': ('wins', 'kills'),
        'escondite': ('wins', 'kills'),
        'thebridge': ('wins', 'kills', 'goals', 'swins', 'skills', 'sgoals',
                      'dwins', 'dkills', 'dgoals', 'twins', 'tkills', 'tgoals')
    }
    for modalidad, sub in modalidades.items():
        for s in sub:
            resultados = []
            for pagina in range(1, 21):
                scraper(pagina, modalidad, s)
                sleep(2)
            insertar_datos_a_db(resultados, modalidad, s)
