import requests
from bs4 import BeautifulSoup
import random
import sys
from time import sleep
from colorama import init, Fore, Back, Style

BASE_NUEVA = './n_hycraft.txt'
BASE_NUEVA2 = './n2_hycraft.txt'
BASE_VIEJA = './hycraft.txt'

def eliminar_duplicados():
    with open(BASE_NUEVA, 'r') as archivo:
        ingestion = archivo.readlines()
    tuple_list = []
    for i in ingestion:
        div = (i.replace('\n', '')).split(' ')
        if len(div) != 2:
            raise ValueError
        tupla = (div[0], div[1])
        tuple_list.append(tupla)
    
    seen_keys = set()
    unique_tuples = []

    for key, value in tuple_list:
        key = key.lower()
        if key not in seen_keys:
            unique_tuples.append((key, value))
            seen_keys.add(key)

    with open(BASE_NUEVA2, 'w') as archivo:
        for i in unique_tuples:
            archivo.write(f'{i[0]} {i[1]}\n')

    
def ingest_data(txt):
    with open(BASE_VIEJA, "r") as file:
        # Read the contents of the file
        data = file.read()
    
    # Split the data by lines
    lines = data.strip().split('\n')
    
    # Initialize variables to store nicknames and passwords
    nicknames = []
    passwords = []
    
    # Iterate over the lines
    for line in lines:
        # Check if the line contains 'nick' or 'password'
        if 'nick:' in line:
            # Extract the nickname and remove leading/trailing whitespace and double quotes
            nickname = line.split(': ')[1].strip().strip('"')
            nicknames.append(nickname)
        elif 'password:' in line:
            # Extract the password and remove leading/trailing whitespace and double quotes
            password = line.split(': ')[1].strip().strip('"')
            passwords.append(password)
    
    # Return the extracted nicknames and passwords as a list of tuples
    lista = list(zip(nicknames, passwords))
    random.shuffle(lista)
    return lista


def rewrite_data(data):
    with open(BASE_NUEVA, 'w') as archivo:
        for i in data:
            archivo.write(f'{i[0]} {i[1]}\n')
    return



def unistats(nick: str) -> bool:
    url = "https://stats.universocraft.com/jugador/" + nick
    headers = {
        'User-Agent': 'BOT'
    }

    session = requests.Session()
    session.headers.update(headers)
    try:
        respuesta = session.get(url)
        respuesta.raise_for_status() # Errores HTTP
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return 'ERROR'
    
    url_error = "https://stats.universocraft.com/?error=true"
    if respuesta.url == url_error:
        return 'NO ENCONTRADO'

    pagina = BeautifulSoup(respuesta.content, 'html.parser')

    tag_premium = pagina.find('span', class_="ProfileTag TagPremium")
    if tag_premium:
        return 'PREMIUM'
    
    tag_rango = pagina.find('span', class_="ProfileTag TagRank")
    rango = tag_rango.text.replace('\n', '').replace(' ', '')
    if rango == 'USU':
        return 'USU'
    else:
        return rango


FINAL = './hycraft.txt'

if __name__ == '__main__':
    encontrado = False
    if len(sys.argv) > 1:
        obj = sys.argv[1]
        print(obj)
    else:
        encontrado = True
        with open(BASE_NUEVA2, 'r') as archivo:
            data = archivo.readlines()
            try:
                for i in data:
                    with open(FINAL, 'a') as final:
                        linea = i.split()
                        nick = linea[0]
                        passw = linea[1]
                        if encontrado == False:
                            if nick.lower() == obj.lower():
                                encontrado = True
                            continue
                        while True:
                            r = unistats(nick)
                            if r == "ERROR":
                                sleep(5)
                            else:
                                break
                            
                        s = "{:<16} {:<16} {}\n".format(nick, passw, r)
                        if r not in ('USU', 'ERROR', 'PREMIUM', 'NO ENCONTRADO'):
                            final.write(s)
                            s = "{:<16} {:<16} {}{}{}\n".format(nick, passw, Fore.GREEN, r, Style.RESET_ALL)
                        else:
                            s = "{:<16} {:<16} {}{}{}\n".format(nick, passw, Fore.RED, r, Style.RESET_ALL)
                        print(s, end='')
                        sleep(1.2)
            except KeyboardInterrupt:
                print(f"\n{nick}")

