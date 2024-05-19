import requests
from bs4 import BeautifulSoup
import schedule
import time
import re
from pathlib import Path
from datetime import datetime
from unistats_scraper import es_premium

URL = 'https://tienda.universocraft.com/'
FICHERO = Path('./rangos.txt')

class Entrada:
    def __init__(self, usuario: str, rango_anterior: str, rango_nuevo: str,duracion: str):
        self.usuario = usuario
        self.rango_anterior = rango_anterior
        self.rango_nuevo = rango_nuevo
        self.duracion = duracion

    def __eq__(self, other):
        return (self.usuario == other.usuario) and (self.rango_anterior == other.rango_anterior) and (self.rango_nuevo == other.rango_nuevo) and (self.duracion == other.duracion)

    def __str__(self):
        if es_premium(self.usuario):
            s = 'PREMIUM'
        else:
            s = 'NO_PREMIUM'
        fecha = datetime.now().strftime("%Y/%m/%d %H:%M")
        if self.rango_anterior and not self.duracion:
            return f"{fecha} {self.usuario} {self.rango_anterior} a {self.rango_nuevo} {s}\n"
        return f"{fecha} {self.usuario} {self.rango_nuevo} {self.duracion} {s}\n"
    


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
        s.pop()
        if i != 'NF\n':
            if len(s) == 6:
                contenido_fichero2.append(Entrada(s[2], s[3], s[5], None))
            else:
                contenido_fichero2.append(Entrada(s[2], None, s[3], s[4]))
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
        if s:
            rangos.append(s)

    rangos2 = []
    for i in rangos:
        encontrado = False
        for j in contenido_fichero:
            if i == j:
                encontrado = True
        if not encontrado:
            rangos2.append(i)
    rangos2.reverse()

    with open(FICHERO, 'a', encoding='utf-8') as archivo:
        for i in rangos2:
            archivo.write(str(i))
        if not encontrado and len(contenido_fichero2) != 0:
            print("Rango anterior no encontrado")
            archivo.write("NF\n")
    print("Lectura completada")
    return


def parsear_string_de_rango(s: str) -> Entrada:
    s = s.rstrip()
    s = s.replace('-', '') # Borrar guiones
    s = re.sub(r'\s+', ' ', s) # Borrar espacios duplicados
    s = s.split(' ') # Dividir
    lista_rangos = ('Júpiter', 'Neptuno', 'Mercurio', 'Saturno')
    if '1' in s[2] and 'Mes' in s[3]:
        s[2] = 'MENSUAL'
        s.pop(3)
    username = s[0]
    if s[1] not in lista_rangos:
        return None
    if s[2].lower() == 'a':
        rango_anterior = s[1]
        rango_nuevo = s[3]
        duracion = None
    else:
        rango_anterior = None
        rango_nuevo = s[1]
        duracion = s[2]
    if duracion and 'PERMANENTE' in duracion:
        duracion = 'PERMANENTE'
    return Entrada(username, rango_anterior, rango_nuevo, duracion)

def schedulef():
    schedule.every(1).minutes.do(scrape)
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    scrape()
    schedulef()