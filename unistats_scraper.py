import requests
from bs4 import BeautifulSoup



def scraper(nick: str) -> bool:
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
        return False
    
    url_error = "https://stats.universocraft.com/?error=true"
    if respuesta.url == url_error:
        print("Usuario no existente - Error de unistats")

    pagina = BeautifulSoup(respuesta.content, 'html.parser')

    tag_premium = pagina.find('span', class_="ProfileTag TagPremium")
    if tag_premium:
        return True
    else:
        return False
    
if __name__ == '__main__':
    print(es_premium('aaa'))