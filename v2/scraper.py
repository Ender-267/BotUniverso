from bs4 import BeautifulSoup
from time import sleep
import sqlite3
import locale
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import urllib3

BASE_DE_DATOS_SQL = './v2/base.db'
TXT_HYCRAFT = './v2/hycraft.txt'

def lanzar_navegador():
    opciones = Options()
    #opciones.add_argument("--headless")
    driver = webdriver.Firefox(options=opciones)
    sleep(10)
    return driver

def captcha(nav: webdriver.Firefox):
    iframe = nav.find_elements(By.TAG_NAME, "iframe")
    if iframe:
        nav.switch_to.frame(iframe[0])
        inputs = nav.find_elements(By.TAG_NAME,"input")
        nav.switch_to.default_content()
        for i in inputs:
            atributo = i.get_attribute("type")
            print(atributo)
            if atributo == "checkbox":
                break
        captcha = i
        captcha.click()
        sleep(5)
    sleep(3)

def detectar_404(nav: webdriver.Firefox):
    es_404 = False
    pres = nav.find_elements(By.TAG_NAME, 'pre')
    for i in pres:
        atributo = i.get_attribute("style")
        if atributo == "word-wrap: break-word; white-space: pre-wrap;":
            es_404 = True
            break
    return es_404

def unistats(nick: str, nav: webdriver.Firefox):
    url = "https://stats.universocraft.com/jugador/" + nick
    url_error = 'https://stats.universocraft.com/?error=true'
    nav.get(url)
    sleep(1.2)
    pagina = BeautifulSoup(nav.page_source, 'html.parser')
    if detectar_404(nav):
        print("Error 404")
        return 'ERROR'
    tag_rango = pagina.find('span', class_="ProfileTag TagRank")
    while not tag_rango and nav.current_url != url_error:
        sleep(3)
        captcha(nav)
        tag_rango = pagina.find('span', class_="ProfileTag TagRank")
    
    if nav.current_url == url_error:
        return (None, None)
    
    pagina = BeautifulSoup(nav.page_source, 'html.parser')
    tag_premium = pagina.find('span', class_="ProfileTag TagPremium")
    if tag_premium:
        premium = 'SI'
    else:
        premium = 'NO'
    tag_rango = pagina.find('span', class_="ProfileTag TagRank")
    rango = tag_rango.text.replace('\n', '').replace(' ', '')
    return (rango, premium)
    
def scraper():
    global nav
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except locale.Error:
        print("The specified locale is not supported on your system.")
    db = sqlite3.connect(BASE_DE_DATOS_SQL)
    cursor = db.cursor()
    querry = "SELECT usuario FROM usuarios WHERE rango IS NULL ORDER BY RANDOM() LIMIT 1"
    while querry:
        cursor.execute(querry)
        usuario = cursor.fetchone()[0]
        ret = unistats(usuario, nav)
        if ret == 'ERROR':
            continue
        print(f"{usuario}     {ret[0]}     {ret[1]}")




if __name__ == '__main__':
    nav = lanzar_navegador()
    try:
        scraper()
    except KeyboardInterrupt:
        nav.close
    nav.close()