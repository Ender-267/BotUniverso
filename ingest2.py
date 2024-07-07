import sqlite3
import json
import re

import re._constants

HASH_20711 = re.compile(r'\$SHA\$[0-9a-f]{16}\$[0-9a-f]{64}')   # Authme SHA256
HASH_2600 = re.compile(r'^[0-9a-f]{32}$')    # md5(md5($pass))
HASH_20710 = re.compile(r'^[0-9a-f]{64}:[^\s]+$')  # sha256(sha256($pass).$salt)
HASH_32410 = re.compile(r'^[0-9a-f]{128}:[^\s]+$')   # sha512(sha512($pass).$salt)
HASH_1700 = re.compile(r'^[0-9a-f]{128}$')  # SHA2-512
HASH_1400 = re.compile(r'^[0-9a-f]{64}$')   # SHA2-256
HASH_REDELEGIT = re.compile(r'\$SHA256\$([a-fA-F0-9]+)@(.+)')   # Hash raro de RedeLegit pero se puede convertir a 20710
HASH_3200 = re.compile(r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$') # bcrypt $2*$, Blowfish (Unix) || BTW esto tarda cantidades aburdas de tiempo en deshashar (años)
HASH_EARTHSKY = re.compile(r'^SHA256\$[a-f0-9]+\$[a-f0-9]+$') # Hash raro de EarthSky pero se puede convertir a 20711

IPV4_REGEX = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

def detectar_hash(hash):
    if not hash:
        return -99
    if re.match(HASH_20711, hash):
        return 20711
    if re.match(HASH_2600, hash):
        return 2600
    if re.match(HASH_20710, hash):
        return 20710
    if re.match(HASH_32410, hash):
        return 32410
    if re.match(HASH_1700, hash):
        return 1700
    if re.match(HASH_1400, hash):
        return 1400
    if re.match(HASH_REDELEGIT, hash):
        return -20710
    if re.match(HASH_3200, hash):
        return 3200
    return -1

def convertir_hash_redelegit_a_20710(hash_original):
    if not hash_original:
        return None
    match = re.search(HASH_REDELEGIT, hash_original)
    if match:
        hash = match.group(1)
        salt = match.group(2)
        hash_convertido = f"{hash}:{salt}"
        return hash_convertido
    else:
        return hash_original
    
import re

def ingesta_generica(file):
    datos_ingestados = []
    for line in file:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            usuario = parts[0].strip().lower()
            contraseña = parts[2].strip() if parts[2].strip() else None
            ip = parts[3].strip() if parts[3].strip() else None
            if ip and not re.match(IPV4_REGEX, ip):
                ip = None
            if not ip and not contraseña:
                continue
            datos_ingestados.append((usuario, contraseña, ip))
    return datos_ingestados

def ingesta_generica2(file):
    datos_ingestados = []
    for line in file:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            usuario = parts[0].strip().lower()
            contraseña = parts[2].strip() if parts[2].strip() else None
            ips = parts[3].strip() if parts[3].strip() else None
            if not ips and not contraseña:
                continue
            if ips:
                ips = ips.split('-')
                ip1 = ips[0].strip()
                if len(ips) == 2:
                    ip2 = ips[1].strip()
                else:
                    ip2 = None
                if ip1 and ('null' in ip1 or not re.match(IPV4_REGEX, ip1)):
                    ip1 = None
                if ip2 and ('null' in ip2 or not re.match(IPV4_REGEX, ip2)):
                    ip2 = None
                if ip1 == ip2:
                    ip2 = None
                if ip1:
                    datos_ingestados.append((usuario, contraseña, ip1))
                if ip2:
                    datos_ingestados.append((usuario, contraseña, ip2))
    return datos_ingestados    

def convertir_hash_earthsky_a_20710(hash_original):
    if not hash_original:
        return None
    HASH_EARTHSKY = r'^SHA256\$([a-f0-9]+)\$([a-f0-9]+)$'
    match = re.search(HASH_EARTHSKY, hash_original)
    if match:
        hash_value = match.group(2)
        salt_value = match.group(1)
        hash_convertido = f"{hash_value}:{salt_value}"
        return hash_convertido
    else:
        return hash_original

def crear_db_nueva():
    with sqlite3.connect('base_v3.db') as db:
        cur = db.cursor()
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario TEXT PRIMARY KEY,
                rango TEXT,
                fecha_ultima_con DATE,
                fecha_primer_login DATE,
                fecha_lectura DATE,
                premium TEXT,
                CONSTRAINT check_dates CHECK (rango IS NULL OR fecha_lectura IS NOT NULL)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS datos (
                id INTEGER PRIMARY KEY,
                usuario TEXT NOT NULL,
                contra TEXT NOT NULL,
                ip TEXT,
                tipo_contra INTEGER NOT NULL,
                db_proveniente TEXTO NOT NULL,
                FOREIGN KEY (usuario) REFERENCES usuarios(usuario)
            )
        ''')
        db.commit()

def migrar_datos():
    con_fuente = sqlite3.connect('neobase.db')
    con_objetivo = sqlite3.connect('base_v3.db')

    try:
        cur_fuente = con_fuente.cursor()
        cur_objetivo = con_objetivo.cursor()

        cur_fuente.execute("SELECT usuario, rango, fecha_ultima_con, fecha_primer_login, fecha_lectura, premium FROM usuarios")
        usuarios = cur_fuente.fetchall()

        datos_usuarios = []
        for usuario in usuarios:
            nick = usuario[0]
            rango = usuario[1]
            fecha_ultima_con = usuario[2]
            fecha_primer_login = usuario[3]
            fecha_lectura = usuario[4]
            premium = usuario[5]
            insertar = (nick, rango, fecha_ultima_con, fecha_primer_login, fecha_lectura, premium)
            datos_usuarios.append(insertar)

        cur_objetivo.executemany(
            "INSERT INTO usuarios (usuario, rango, fecha_ultima_con, fecha_primer_login, fecha_lectura, premium) VALUES (?, ?, ?, ?, ?, ?)",
            datos_usuarios
        )

        con_objetivo.commit()

    except Exception as e:
        con_objetivo.rollback()
        print(f"An error occurred: {e}")

    finally:
        # Close the connections
        con_fuente.close()
        con_objetivo.close()

BASE_DE_DATOS_SQL = './base_v3.db'
TXT_HYCRAFT = './bases/hycraft.txt'
TXT_OMEGACRAFT = './bases/OmegaCraft.json'
TXT_EXCALIBURCRAFT = 'C:/Users/Alberto/Downloads/DB MC/DB MC/ExcaliburCraft - AuthMe.txt'
TXT_HYPERMINE = 'C:/Users/Alberto/Downloads/DB MC/DB MC/HyperMine - AuthMe.txt'
TXT_GAMEMADEINPOLA = 'C:/Users/Alberto/Downloads/DB MC/DB MC/GamesMadeInPola - AuthMe.txt'
TXT_NEMERYA = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Nemerya (2021) - AuthMe.txt'
TXT_FUNCRAFT = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Funcraft - AuthMe.txt'
TXT_REDELEGIT = 'C:/Users/Alberto/Downloads/DB MC/DB MC/RedeLegit - nLogin.txt'
TXT_ECUACRAFT_LOGIN = 'C:/Users/Alberto/Downloads/DB MC/DB MC/EcuaCraft - Login.txt'
TXT_ECUACRAFT_AUTHME = 'C:/Users/Alberto/Downloads/DB MC/DB MC/EcuaCraft - AuthMe.txt'
TXT_HEALFIGHT = 'C:/Users/Alberto/Downloads/DB MC/DB MC/HealFight - AuthMe.txt'
TXT_CRAFTYOURLIFE = 'C:/Users/Alberto/Downloads/DB MC/DB MC/CraftYourLife -  Passwords.txt'
TXT_PANDAKMC = 'C:/Users/Alberto/Downloads/DB MC/DB MC/PandakMC - Authme.txt'
TXT_VELYSIAMC = 'C:/Users/Alberto/Downloads/DB MC/DB MC/VelysiaMC - AuthMe.txt'
TXT_ZEOLIA = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Zeolia - AuthMe.txt'
TXT_ECLOZIA = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Eclozia.txt'
TXT_SKYCRAFT = 'C:/Users/Alberto/Downloads/DB MC/DB MC/SkyCraft - AuthMe.txt'
TXT_PACTIFY = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Pactify11k 2021 (User,Dehash,IP).txt'
TXT_VALERIA = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Varelia_-_Authme.txt'
TXT_EDENRIO = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Edenrio_-_Authme.txt'
TXT_BATTLEADVENTURE = 'C:/Users/Alberto/Downloads/DB MC/DB MC/BattleAdventure - JPremium.txt'
TXT_EARTHSKY = 'C:/Users/Alberto/Downloads/DB MC/DB MC/EarthSky - JPremium.txt'
TXT_RUSHY = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Rushy_-_Authme.txt'
TXT_ZOROTEXT = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Zorotex - AuthMe.txt'
TXT_INFARIUM = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Infarium_-_AuthMe.txt'
TXT_VELYSIAMC = 'C:/Users/Alberto/Downloads/DB MC/DB MC/VelysiaMC - AuthMe.txt'
TXT_WAIRAMC = 'C:/Users/Alberto/Downloads/DB MC/DB MC/WariaMC - AuthMe.txt'
TXT_MONDIALCRAFT = 'C:/Users/Alberto/Downloads/DB MC/DB MC/MondialCraft_-_Authme.txt'
TXT_SUNLYWORLD = 'C:/Users/Alberto/Downloads/DB MC/DB MC/SunlyWorld - Authme.txt'
TXT_ANDARIUM = 'C:/Users/Alberto/Downloads/DB MC/DB MC/Andarium_-_Authme.txt'
TXT_DISCOVERYCRAFT = 'C:/Users/Alberto/Downloads/DB MC/DB MC/DiscoveryCraft_-_Login.txt'
TXT_KNOWLESMC = 'C:/Users/Alberto/Downloads/DB MC/DB MC/KnowlesMC JPremium Cracks.txt'
TXT_EVONICRAFT = 'C:/Users/Alberto/Downloads/DB MC/DB MC/EvoniCraft - AuthMe.txt'



def ingestar_omegacraft():
    with open(TXT_OMEGACRAFT, 'r') as file:
        datos = json.load(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos:
            nick = dato['name'].lower()
            contra = dato['password']
            ip = dato['ip']
            if 'Not Found' in ip:
                ip = None
            if ip and not re.match(IPV4_REGEX, ip):
                ip = None
            if not ip and not contra:
                continue
            tipo_contra = detectar_hash(contra)
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (nick, contra, ip, tipo_contra, 'OMEGACRAFT'))
            
        db.commit()


def ingestar_hycraft():
    datos_ingestados = []
    with open(TXT_HYCRAFT, 'r', encoding='utf-8') as archivo:
        datos = []
        for linea in archivo:
            if linea == '-\n':
                if len(datos) == 3:
                    datos_ingestados.append(tuple(datos))
                datos = []
            if 'nick:' in linea:
                nick = str(linea.split(':', 1)[1].strip().strip('"').lower())
                datos.append(nick)
            if 'password:' in linea:
                contra = str(linea.split(':', 1)[1].strip().strip('"'))
                datos.append(contra)
            if 'ip:' in linea:
                ip = str(linea.split(':', 1)[1].strip().strip('"'))
                if ip and not re.match(IPV4_REGEX, ip):
                    ip = None
                datos.append(ip)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            nick = dato[0]
            contra = dato[1]
            ip = dato[2]
            if not contra and not ip:
                continue
            tipo_contra = detectar_hash(contra)
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (nick, contra, ip, tipo_contra, 'HYCRAFT'))


def ingestar_excaliburcraft():
    with open(TXT_EXCALIBURCRAFT, 'r', encoding='utf-8') as file:
        datos_ingestados = []
        for line in file:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                usuario = parts[0].strip().lower()
                contraseña = parts[2].strip() if parts[2].strip() else None
                if not contraseña:
                    continue
                datos_ingestados.append((usuario, contraseña))

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], None, tipo_contra, 'EXCALIBURCRAFT'))

        db.commit()

def ingestar_hypermine():
    with open(TXT_HYPERMINE, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'HYPERMINE'))

        db.commit()

def ingestar_gamesmadeinpola():
    with open(TXT_GAMEMADEINPOLA, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            if tipo_contra == 1700:
                tipo_contra = -2
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'GAMESMADEINPOLA'))

def ingestar_nemerya():
    with open(TXT_NEMERYA, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'NEMERYA'))

def ingestar_funcraft():
    with open(TXT_FUNCRAFT, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'FUNCRAFT'))

def ingestar_redelegit():
    with open(TXT_REDELEGIT, 'r', encoding='utf-8') as file:
        datos_ingestados = []
        for line in file:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                usuario = parts[0].strip().lower()
                contraseña = parts[2].strip() if parts[2].strip() else None
                if contraseña:
                    contraseña = convertir_hash_redelegit_a_20710(contraseña)
                ip = parts[3].strip() if parts[3].strip() else None
                if ip and not re.match(IPV4_REGEX, ip):
                    ip = None
                if not ip and not contraseña:
                    continue
                datos_ingestados.append((usuario, contraseña, ip))

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'REDELEGIT'))

def ingestar_ecuacraft_login():
    with open(TXT_ECUACRAFT_LOGIN, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'ECUACRAFT'))

def ingestar_ecuacraft_authme():
    with open(TXT_ECUACRAFT_AUTHME, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'ECUACRAFT'))

def ingestar_healfight():
    with open(TXT_HEALFIGHT, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica2(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'HEALFIGHT'))

def ingestar_craftyourlife():
    with open(TXT_CRAFTYOURLIFE, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'CRAFTYOURLIFE'))

def ingestar_pandakmc():
    with open(TXT_PANDAKMC, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica2(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'PANDAKMC'))

def ingestar_velysiamc():
    with open(TXT_VELYSIAMC, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica2(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'VELYSIAMC'))

def ingestar_zeolia():
    with open(TXT_ZEOLIA, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica2(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'ZEOLIA'))

def ingestar_eclozia():
    with open(TXT_ECLOZIA, 'r', encoding='utf-8') as file:
        datos_ingestados = []
        for line in file:
            parts = line.strip().split(',')
            if ',Eclozia,' in line:
                if len(parts) >= 5:
                    usuario = parts[2].strip().lower()
                    contraseña = parts[4].strip() if parts[4].strip() else None
                    ip = parts[5].strip() if parts[5].strip() else None
                    if ip and not re.match(IPV4_REGEX, ip):
                        ip = None
                    if not ip and not contraseña:
                        continue
                    datos_ingestados.append((usuario, contraseña, ip))
            else:
                if len(parts) >= 4:
                    usuario = parts[0].strip().lower()
                    contraseña = parts[2].strip() if parts[2].strip() else None
                    ip = parts[3].strip() if parts[3].strip() else None
                    if ip and not re.match(IPV4_REGEX, ip):
                        ip = None
                    if not ip and not contraseña:
                        continue
                    datos_ingestados.append((usuario, contraseña, ip))

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'ECLOZIA'))

def ingestar_skycraft():
    with open(TXT_SKYCRAFT, 'r', encoding='latin-1') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'SKYCRAFT'))

def ingestar_pactify():
    with open(TXT_PACTIFY, 'r', encoding='latin-1') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'PACTIFY'))

def ingestar_valeria():
    with open(TXT_VALERIA, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica2(file)
    
    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
            cur = db.cursor()
            for dato in datos_ingestados:
                tipo_contra = detectar_hash(dato[1])
                cur.execute('''
                    INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
                ''', (dato[0], dato[1], dato[2], tipo_contra, 'VALERIA'))

def ingestar_edenrio():
    with open(TXT_EDENRIO, 'r', encoding='latin-1') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'EDENRIO'))

def ingestar_battleadventure():
    with open(TXT_BATTLEADVENTURE, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            if tipo_contra == 1700:
                tipo_contra = -2
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'BATTLEADVENTURE'))

def ingestar_earthsky():
    with open(TXT_EARTHSKY, 'r', encoding='utf-8') as file:
        datos_ingestados = []
        for line in file:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                usuario = parts[0].strip().lower()
                contraseña = parts[2].strip() if parts[2].strip() else None
                contraseña = convertir_hash_earthsky_a_20710(contraseña)
                ips = parts[3].strip() if parts[3].strip() else None
                ips = ips.split('-')
                ip1 = ips[0].strip()
                if len(ips) == 2:
                    ip2 = ips[1].strip()
                else:
                    ip2 = None
                if not ips and not contraseña:
                    continue
                if ip1 and ('null' in ip1 or not re.match(IPV4_REGEX, ip1)):
                    ip1 = None
                if ip2 and ('null' in ip2 or not re.match(IPV4_REGEX, ip2)):
                    ip2 = None
                if ip1 == ip2:
                    ip2 = None
                if ip1:
                    datos_ingestados.append((usuario, contraseña, ip1))
                if ip2:
                    datos_ingestados.append((usuario, contraseña, ip2))
    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'EARTHSKY'))

def ingestar_rushy():
    with open(TXT_RUSHY, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica2(file)
    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'RUSHY'))

def ingestar_zorotex():
    with open(TXT_ZOROTEXT, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'ZOROTEX'))

def ingestar_infarium():
    with open(TXT_INFARIUM, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'INFARIUM'))

def ingestar_velysiamc():
    with open(TXT_VELYSIAMC, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica2(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'VELYSIAMC'))

def ingestar_wariamc():
    with open(TXT_WAIRAMC, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'WARIAMC'))

def ingestar_mondialcraft():
    with open(TXT_MONDIALCRAFT, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica2(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'MONDIALCRAFT'))

def ingestar_sunlyworld():
    with open(TXT_SUNLYWORLD, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'SUNLYWORLD'))

def ingestar_andarium():
    with open(TXT_ANDARIUM, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'ANDARIUM'))

def ingestar_discoverycraft():
    with open(TXT_DISCOVERYCRAFT, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            if tipo_contra == 1700:
                tipo_contra = -2
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'DISCOVERYCRAFT'))

def ingestar_knowlesmc():
    with open(TXT_KNOWLESMC, 'r', encoding='utf-8') as file:
        datos_ingestados = []
        for line in file:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                usuario = parts[0].strip().lower()
                contraseña = parts[2].strip() if parts[2].strip() else None
                contraseña = convertir_hash_earthsky_a_20710(contraseña)
                ips = parts[3].strip() if parts[3].strip() else None
                ips = ips.split('-')
                ip1 = ips[0].strip()
                if len(ips) == 2:
                    ip2 = ips[1].strip()
                else:
                    ip2 = None
                if not ips and not contraseña:
                    continue
                if ip1 and ('null' in ip1 or not re.match(IPV4_REGEX, ip1)):
                    ip1 = None
                if ip2 and ('null' in ip2 or not re.match(IPV4_REGEX, ip2)):
                    ip2 = None
                if ip1 == ip2:
                    ip2 = None
                if ip1:
                    datos_ingestados.append((usuario, contraseña, ip1))
                if ip2:
                    datos_ingestados.append((usuario, contraseña, ip2))
    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'KNOWLESMC'))

def ingestar_evonicraft():
    with open(TXT_EVONICRAFT, 'r', encoding='utf-8') as file:
        datos_ingestados = ingesta_generica(file)

    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        for dato in datos_ingestados:
            tipo_contra = detectar_hash(dato[1])
            cur.execute('''
                INSERT OR IGNORE INTO datos (usuario, contra, ip, tipo_contra, db_proveniente) VALUES (?, ?, ?, ?, ?)
            ''', (dato[0], dato[1], dato[2], tipo_contra, 'EVONICRAFT'))

def eliminar_datos_duplicados():
    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        cur.execute('''DELETE FROM datos
                        WHERE rowid NOT IN (
                            SELECT MIN(rowid)
                            FROM datos
                            GROUP BY usuario, contra, ip, db_proveniente
                        )'''
                    )
        db.commit()

def generar_usuarios_restantes():
    with sqlite3.connect(BASE_DE_DATOS_SQL) as db:
        cur = db.cursor()
        cur.execute('''
            SELECT d.usuario
            FROM datos d
            LEFT JOIN usuarios u ON d.usuario = u.usuario
            WHERE u.usuario IS NULL
        ''')
        usuarios_unicos = cur.fetchall()
        usuarios_unicos = list(set(usuarios_unicos))
        cur.executemany("INSERT OR IGNORE INTO usuarios (usuario) VALUES (?)", usuarios_unicos)
        db.commit()

def limpiar_usuarios_no_validos():
    with sqlite3.connect('base_v3.db') as db:
        cur = db.cursor()
        regex_pattern = re.compile(r'^[a-z0-9_]{3,16}$')
        cur.execute('''
            SELECT usuario
            FROM usuarios
        ''')

        columnas = cur.fetchall()
        for usuario in columnas:
            if not re.match(regex_pattern, usuario[0]):
                cur.execute('''
                    DELETE FROM usuarios WHERE usuario=?
                    ''', (usuario[0], ))
                cur.execute('''
                    DELETE FROM datos WHERE usuario=?
                    ''', (usuario[0], ))
        db.commit()

if __name__ == '__main__':
    ingestar_zeolia()
    ingestar_eclozia()
    ingestar_skycraft()
    ingestar_pactify()
    ingestar_valeria()
    ingestar_edenrio()
    ingestar_battleadventure()
    ingestar_earthsky()
    ingestar_rushy()
    ingestar_zorotex()
    ingestar_infarium()
    ingestar_velysiamc()
    ingestar_wariamc()
    ingestar_mondialcraft()
    ingestar_sunlyworld()
    ingestar_andarium()
    ingestar_discoverycraft()
    ingestar_knowlesmc()
    ingestar_evonicraft()

    limpiar_usuarios_no_validos()
    eliminar_datos_duplicados()
    generar_usuarios_restantes()

