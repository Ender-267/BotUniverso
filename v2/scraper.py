from bs4 import BeautifulSoup
from time import sleep
import sqlite3
import requests
import locale
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

BASE_DE_DATOS_SQL = './v2/base.db'
TXT_HYCRAFT = './v2/hycraft.txt'

def cf_captcha():
    driver = webdriver.Chrome()
    driver.get("https://stats.universocraft.com/jugador/Ender267")
    captcha_pasado = 0
    sleep(1000)
    while captcha_pasado != 2:
        sleep(3)
        iframe = driver.find_elements(By.TAG_NAME, "iframe")
        if iframe:
            if captcha_pasado == 0:
                driver.switch_to.frame(iframe[0])
            captcha_pasado = 1
            inputs = driver.find_elements(By.TAG_NAME,"input")
            for i in inputs:
                atributo = i.get_attribute("type")
                print(atributo)
                if atributo == "checkbox":
                    break
            captcha = i
            captcha.click()
            sleep(10)
        iframe = driver.find_elements(By.TAG_NAME, "iframe")
        if not iframe:
            captcha_pasado = 2

    driver.refresh()
    alerta = driver.switch_to.alert
    alerta.accept()
    cookie = driver.get_cookie('cf_clearance')
    return f"{cookie["name"]}={cookie["value"]}"

def unistats(nick: str, token: str) -> tuple | str:
    url = "https://stats.universocraft.com/jugador/" + nick
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
        "Connection": "keep-alive",
        "Content-Length": "5031",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "cf_clearance=X3pOxWsENxU5yxKbv425cBdqFlAg59Nan4DaNLk9jb8-1717463427-1.0.1.1-slQEhvZ2T1iSC.V6S9z_O0_mzdT9CvqOLoLUBncviiJLNKQuiFge50jEzjIPqvqag4b_yifrx4kAd5A3c.dWQg",
        "Host": "stats.universocraft.com",
        "Origin": "https://stats.universocraft.com",
        "Priority": "u=1",
        "Referer": "https://stats.universocraft.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "TE": "trailers",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0"
    }





    session = requests.Session()
    session.headers.update(headers)
    try:
        respuesta = session.get(url)
        respuesta.raise_for_status() # Errores HTTP
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return f'ERROR {e}'

    url_error = "https://stats.universocraft.com/?error=true"
    if respuesta.url == url_error:
        return ('NO ENCONTRADO', None)

    
    pagina = BeautifulSoup(respuesta.text, 'html.parser')

    tag_premium = pagina.find('span', class_="ProfileTag TagPremium")
    if tag_premium:
        premium = 'SI'
    else:
        premium = 'NO'
    
    tag_rango = pagina.find('span', class_="ProfileTag TagRank")
    rango = tag_rango.text.replace('\n', '').replace(' ', '')
    return (rango, premium)
    

def scraper():
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
    except locale.Error:
        print("The specified locale is not supported on your system.")
    db = sqlite3.connect(BASE_DE_DATOS_SQL)
    cursor = db.cursor()
    querry = "SELECT usuario FROM usuarios WHERE rango IS NULL LIMIT 1"
    while querry:
        cursor.execute(querry)
        usuario = cursor.fetchone()




if __name__ == '__main__':
    token = cf_captcha()