from bs4 import BeautifulSoup
from time import sleep
import sqlite3
import locale
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import urllib3
from colorama import Fore, Style

BASE_DE_DATOS_SQL = './v2/base.db'
TXT_HYCRAFT = './v2/hycraft.txt'

def lanzar_navegador():
    opciones = Options()
    #opciones.add_argument("--headless")
    driver = webdriver.Firefox(options=opciones)
    sleep(5)
    return driver

def detectar_captcha(nav: webdriver.Firefox):
    iframe = nav.find_elements(By.TAG_NAME, "iframe")
    if iframe:
        print(Fore.CYAN + "Captcha detectado" + Style.RESET_ALL)
        sleep(5)
        iframe = nav.find_elements(By.TAG_NAME, "iframe")
        if iframe:
            nav.switch_to.frame(iframe[0])
            inputs = nav.find_elements(By.TAG_NAME,"input")
            
            for i in inputs:
                atributo = i.get_attribute("type")
                print(atributo)
                if atributo == "checkbox":
                    break
            captcha = i
            captcha.click()
            sleep(5)
            nav.switch_to.default_content()
        return True
    else:
        return False

def unistats(nick: str, nav: webdriver.Firefox):
    url = "https://stats.universocraft.com/jugador/" + nick
    url_error = 'https://stats.universocraft.com/?error=true'
    nav.get(url)
    sleep(1.5)
    detectar_captcha(nav)
    pagina = BeautifulSoup(nav.page_source, 'html.parser')
    tag_rango = pagina.find('span', class_="ProfileTag TagRank")
    tiempo_de_espera = 0
    while not tag_rango and nav.current_url != url_error:
        sleep(0.1)
        tag_rango = pagina.find('span', class_="ProfileTag TagRank")
        tiempo_de_espera += 0.1
        if tiempo_de_espera >= 3:
            print("Error de carga de pagina")
            return unistats(nick, nav)
    if nav.current_url == url_error:
        return (None, None)
    
    tag_premium = pagina.find('span', class_="ProfileTag TagPremium")
    if tag_premium:
        premium = 'SI'
    else:
        premium = 'NO'
    rango = tag_rango.text.replace('\n', '').replace(' ', '')
    return (rango, premium)

def texto_rango(rango:str) -> str:
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
        rango = ret[0]
        premium = ret[1]
        if not premium and not rango:
            print("{:<16} {}NO ENCONTRADO{}".format(usuario, Fore.RED, Style.RESET_ALL))
            continue
        match premium:
            case 'SI':
                texto_premium = "PREMIUM"
            case 'NO':
                texto_premium = "NO_PREMIUM"
            case _:
                texto_premium = "WTF"
        s = "{:<16} {:<8} {:<8}\n".format(usuario, texto_rango(rango), texto_premium)
        print(s, end='')




if __name__ == '__main__':
    nav = lanzar_navegador()
    try:
        scraper()
    except KeyboardInterrupt:
        nav.close
    nav.close()