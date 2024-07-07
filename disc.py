# -*- coding: utf-8 -*-

import discord
from discord.ext import commands, tasks
import json
import sqlite3
from asyncio import sleep
from colorama import Fore, Style
import hashlib
import os
from prettytable import PrettyTable

# Constants
ID_CANAL_TOKEN = 1246869970340806686
TOKEN_TXT = './token.json'
BASE_DATOS = './base_v3.db'

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variable to manage token message
mandar_mensage = True

# Helper function to handle SQLite queries
async def query_con_handling(cur: sqlite3.Cursor, query: str, tupla: tuple = ()):
    try:
        cur.execute(query, tupla)
        cur.connection.commit()
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print(f"{Fore.YELLOW}Base de datos bloqueada{Style.RESET_ALL}")
            await sleep(2)
            return await query_con_handling(cur, query, tupla)
        else:
            raise
    return cur

def crear_archivo(headers, fetchall):
    tabla = PrettyTable()
    tabla.field_names = headers
    tabla.align = 'l'
    for row in fetchall:
        tabla.add_row(row)
    
    tabla_str = tabla.get_string()

    md5_hash = hashlib.md5(tabla_str.encode()).hexdigest()
    nombre_archivo = f"message_buffer/{md5_hash}.txt"

    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        f.write(tabla_str)
    
    return nombre_archivo

# Background task to check token validity
@tasks.loop(seconds=2)
async def comprobar_validez_token():
    global mandar_mensage
    with open(TOKEN_TXT, 'r') as archivo:
        datos = json.load(archivo)
    if datos.get("http_error") and mandar_mensage:
        canal = bot.get_channel(ID_CANAL_TOKEN)
        if canal:
            await canal.send('Inserte token!!')
            mandar_mensage = False

# Command to set token
@bot.command(name='token')
async def set_token(ctx, ip: str, value: str):
    global mandar_mensage
    MAX_HEADER = 2
    try:
        ip = int(ip)
        if not 0 <= ip <= MAX_HEADER:
            raise ValueError
    except Exception:
        await ctx.send(f'Error de id de header')
    with open(TOKEN_TXT, 'w') as archivo:
        jsond = {
            "http_error": False,
            "token": value,
            "header_id": ip
        }
        json.dump(jsond, archivo)
        mandar_mensage = True
    await ctx.send(f'Token se ha actualizado a: {value}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass

# Command to search by nickname
@bot.command(name='nick')
async def nick(ctx, value: str):
    value = value.lower()
    try:
        with sqlite3.connect(BASE_DATOS) as db:
            cur = db.cursor()
            query = "SELECT usuario, contra, ip, db_proveniente, tipo_contra FROM usuarios NATURAL JOIN datos WHERE usuario GLOB ? ORDER BY usuario LIMIT 100000"
            tupla = (value,)
            await query_con_handling(cur, query, tupla)
            rows = cur.fetchall()
            if rows:
                archivo = crear_archivo(('usuario', 'contraseña', 'ip', 'base de datos', 'tipo de hash'), rows)
                await ctx.send(file=discord.File(archivo))
                try:
                    os.remove(archivo)
                except FileNotFoundError:
                    pass
            else:
                await ctx.send("No se encontraron resultados")
    except sqlite3.Error as e:
        await ctx.send(f"Error de SQL: {e}")

# Command to search by IP
@bot.command(name='ip')
async def ip(ctx, value: str):
    value = value.lower()
    try:
        with sqlite3.connect(BASE_DATOS) as db:
            cur = db.cursor()
            query = "SELECT usuario, contra, ip, db_proveniente, tipo_contra FROM usuarios NATURAL JOIN datos WHERE ip GLOB ? ORDER BY ip LIMIT 100000"
            tupla = (value,)
            await query_con_handling(cur, query, tupla)
            rows = cur.fetchall()
            if rows:
                archivo = crear_archivo(('usuario', 'contraseña', 'ip', 'base de datos', 'tipo de hash'), rows)
                await ctx.send(file=discord.File(archivo))
                try:
                    os.remove(archivo)
                except FileNotFoundError:
                    pass
            else:
                await ctx.send("No se encontraron resultados")
    except sqlite3.Error as e:
        await ctx.send(f"Error de SQL: {e}")

@bot.command(name='pass')
async def ip(ctx, value: str):
    try:
        with sqlite3.connect(BASE_DATOS) as db:
            cur = db.cursor()
            query = "SELECT usuario, contra, ip, db_proveniente, tipo_contra FROM usuarios NATURAL JOIN datos WHERE contra GLOB ? ORDER BY contra LIMIT 100000"
            tupla = (value,)
            await query_con_handling(cur, query, tupla)
            rows = cur.fetchall()
            if rows:
                archivo = crear_archivo(('usuario', 'contraseña', 'ip', 'base de datos', 'tipo de hash'), rows)
                await ctx.send(file=discord.File(archivo))
                try:
                    os.remove(archivo)
                except FileNotFoundError:
                    pass
            else:
                await ctx.send("No se encontraron resultados")
    except sqlite3.Error as e:
        await ctx.send(f"Error de SQL: {e}")

# Event triggered when bot is ready
@bot.event
async def on_ready():
    print(f'Logueado como {bot.user}')
    comprobar_validez_token.start()

# Main entry point
if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python filename.py <TOKEN>")
    else:
        token_bot = sys.argv[1]
        bot.run(token_bot)
