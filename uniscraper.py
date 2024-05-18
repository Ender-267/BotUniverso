import requests
from bs4 import BeautifulSoup
import schedule
import time
import re
from pathlib import Path
from datetime import datetime

URL = 'https://tienda.universocraft.com/'
FICHERO = Path('./rangos.txt')

class Entrada:
    def __init__(self, usuario: str, rango: str, duracion: str):
        self.usuario = usuario
        self.rango = rango
        self.duracion = duracion

    def __eq__(self, other):
        return (self.usuario == other.usuario) and (self.rango == other.rango) and (self.duracion == other.duracion)

    def __str__(self):
        fecha = datetime.now().strftime("%Y/%m/%d %H:%M")
        return f"{fecha} {self.usuario} {self.rango} {self.duracion}\n"
    


def scrape():
    contenido_fichero = []
    try:
        with open(FICHERO, 'r', encoding='utf-8') as archivo:
            contenido_fichero = (archivo.readlines())[-50:]
    except FileNotFoundError:
        print("Archivo no encontrado en lectura")

    contenido_fichero2 = []
    for i in contenido_fichero:
        s = i.replace('\n', '')
        s = s.split(' ')
        if i != 'NF\n':
            contenido_fichero2.append(Entrada(s[2], s[3], s[4]))
    contenido_fichero = contenido_fichero2
    
    try:
        respuesta = requests.get(URL)
        respuesta.raise_for_status() # Errores HTTP
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return

    pagina = BeautifulSoup(respuesta.content, 'html.parser')
    lista_h6 = pagina.find_all('h6')
    rangos = []
    encontrado = False
    for tag in lista_h6:
        s = parsear_string_de_rango(tag.get_text())
        rangos.append(s)

    rangos2 = []
    for i in rangos:
        encontrado = False
        for j in contenido_fichero:
            if i == j:
                encontrado = True
        if not encontrado:
            rangos2.append(i)

                

    with open(FICHERO, 'a', encoding='utf-8') as archivo:
        for i in rangos2:
            archivo.write(str(i))
        if not encontrado and len(contenido_fichero2) != 0:
            print("Rango anterior no encontrado")
            archivo.write("NF\n")
    return


def parsear_string_de_rango(s: str) -> Entrada:
    s = re.sub(r'\s+', ' ', s) # Borrar espacios duplicados
    s = s.replace('\n', '') # Borrar saltos de linea
    s = s.split(' ') # Dividir 
    username = s[0]
    rango = s[2]
    duracion = s[3]
    if 'PERMANENTE' in duracion:
        duracion = 'PERMANENTE'
    elif '1' in duracion:
        duracion = 'MENSUAL'
    return Entrada(username, rango, duracion)

def schedulef():
    schedule.every(1).minutes.do(scrape)
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    schedulef()