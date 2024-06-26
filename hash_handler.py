import re
import subprocess
import os
import argparse

def extraer_hashes(archivo_de_entrada):
    try:
        with open(archivo_de_entrada, 'r') as f:
            contenido = f.read()
        
        hashes = re.findall(r'\$SHA\$[^\s\n]+', contenido)
        return hashes, contenido
    except Exception as e:
        print(f"Error leyendo el archivo {archivo_de_entrada}: {e}")
        return [], ""

def escribir_hashes(hashes, salida):
    try:
        with open(salida, 'w') as f:
            for sha_string in hashes:
                f.write(sha_string + '\n')
    except Exception as e:
        print(f"Error escribiendo el archivo {salida}: {e}")

def lanzar_hashcat(comando, dir_hashcat):
    try:
        directorio_original = os.getcwd()
        os.chdir(dir_hashcat)
        
        process = subprocess.Popen(comando, shell=True)
        process.wait()
        
        os.chdir(directorio_original)
    except Exception as e:
        print(f"Error lanzando hashcat: {e}")

def leer_archivo_contras(path):
    reemplazados = {}
    try:
        with open(path, 'r') as f:
            lineas = f.readlines()
            for linea in lineas:
                original, nuevo = linea.strip().split(':')
                reemplazados[original] = nuevo
    except Exception as e:
        print(f"Error leyendo el archivo {path}: {e}")
    return reemplazados

def reemplazar_hashes(contenido, reemplazados):
    for original, nuevo in reemplazados.items():
        contenido = contenido.replace(original, nuevo)
    return contenido

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Procesar el archivo rangos para reemplazar hashes con hashcat.')
    parser.add_argument('rangos', help='Ruta del archivo de entrada con los rangos')
    args = parser.parse_args()

    DIR_HASHCAT = r"C:/Users/Alberto/Documents/hashcat/"
    rangos = args.rangos
    hashes_path = os.path.join(DIR_HASHCAT, "auto_hashes.txt")
    cracked = os.path.join(DIR_HASHCAT, "auto_cracked.txt")
    hashcat = f"hashcat.exe --potfile-disable -m 20711 -a 0 -O -o {cracked} {hashes_path} weakpass_3a"
    
    # Extraer hashes del archivo de entrada
    hashes, contenido = extraer_hashes(rangos)
    
    # Escribir los hashes extraídos en un archivo de salida
    escribir_hashes(hashes, hashes_path)
    
    # Clear the auto_cracked.txt file
    try:
        with open(cracked, 'w') as f:
            f.write('')
    except Exception as e:
        print(f"Error limpiando el archivo {cracked}: {e}")
    
    # Lanzar hashcat con el comando especificado
    
    lanzar_hashcat(hashcat, DIR_HASHCAT)

    # Leer el archivo de contraseñas crackeadas
    reemplazados = leer_archivo_contras(cracked)
    
    # Reemplazar los hashes originales con las nuevas contraseñas en el contenido
    nuevo_contenido = reemplazar_hashes(contenido, reemplazados)
    
    # Escribir el nuevo contenido en el archivo de entrada original
    try:
        with open(rangos, 'w') as f:
            f.write(nuevo_contenido)
    except Exception as e:
        print(f"Error escribiendo el archivo {rangos}: {e}")
