from bs4 import BeautifulSoup
from time import sleep
import sqlite3
import locale
from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib3

BASE_DE_DATOS_SQL = './v2/base.db'
TXT_HYCRAFT = './v2/hycraft.txt'

def cf_captcha():
    driver = webdriver.Firefox()
    driver.get("https://stats.universocraft.com/jugador/Ender267")

    iframe = driver.find_elements(By.TAG_NAME, "iframe")
    if iframe:
        driver.switch_to.frame(iframe[0])
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


    driver.refresh()
    alerta = driver.switch_to.alert
    alerta.accept()
    cookie = driver.get_cookie('cf_clearance')
    return f"{cookie["name"]}={cookie["value"]}"

def unistats(nick: str, token: str) -> tuple | str:
    url = "https://stats.universocraft.com/jugador/" + nick
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, zstd",
        "Accept-Language": "es-ES,es;q=0.9",
        "Cache-Control": "max-age=0",
        "Cookie": "cf_clearance=ODqtjvhD5W0W4r.A13oBF.p7FgNzZkaIvO_Bg8oZYnc-1717466413-1.0.1.1-61tXKKl4vO0NAI.x6NY_FlAEmXwukJNPSBc4yjYesq0c9yHYwcwTwZzbIgAvnsRKrcL_uFCgPmciQY3_sXZQ8w",
        "Priority": "u=0, i",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Brave";v="126"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Model": '""',
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Ch-Ua-Platform-Version": '"15.0.0"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-Gpc": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    sesion = urllib3.PoolManager()
    try:
        respuesta = sesion.request('GET', url, headers=headers)
        sleep(2)
        respuesta = sesion.request('GET', url, headers=headers)
    except urllib3.exceptions.HTTPError as e:
        print(f"Error fetching the webpage: {e}")
        return f'ERROR {e}'


    url_error = "https://stats.universocraft.com/?error=true"
    if respuesta.geturl() == url_error:
        return ('NO ENCONTRADO', None)

    print(respuesta.status)
    pagina = BeautifulSoup(respuesta.data, 'html.parser')
    print(pagina.prettify())
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
    unistats('Ender267', None)