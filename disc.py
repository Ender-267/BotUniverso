import discord
from discord.ext import commands, tasks
import json
import sqlite3
from asyncio import sleep
from colorama import Fore, Style

# Constants
ID_CANAL_TOKEN = 1246869970340806686
TOKEN_TXT = './token.json'
BASE_DATOS = './base.db'

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
    MAX_HEADER = 1
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

# Command to search by nickname
@bot.command(name='nick')
async def nick(ctx, value: str):
    value = value.lower()
    try:
        with sqlite3.connect(BASE_DATOS) as db:
            cur = db.cursor()
            query = "SELECT contra, ip FROM usuarios NATURAL JOIN datos WHERE usuario = ?"
            tupla = (value,)
            await query_con_handling(cur, query, tupla)
            
            rows = cur.fetchall()
            if rows:
                msgs = []
                current_msg = "```\n"
                for row in rows:
                    line = f"contra: {row[0]}, ip: {row[1]}\n"
                    if len(current_msg) + len(line) + 3 > 2000:
                        current_msg += "```"
                        msgs.append(current_msg)
                        current_msg = "```\n" + line
                    else:
                        current_msg += line
                if current_msg:
                    current_msg += "```"
                    msgs.append(current_msg)
                
                for msg in msgs:
                    await ctx.send(msg)
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
            query = "SELECT contra, usuario FROM usuarios NATURAL JOIN datos WHERE ip = ?"
            tupla = (value,)
            await query_con_handling(cur, query, tupla)
            
            rows = cur.fetchall()
            if rows:
                msgs = []
                current_msg = "```\n"
                for row in rows:
                    line = f"nick: {row[1]}, contra: {row[0]}\n"
                    if len(current_msg) + len(line) + 3 > 2000:  # Adding 3 for closing backticks
                        current_msg += "```"
                        msgs.append(current_msg)
                        current_msg = "```\n" + line
                    else:
                        current_msg += line
                if current_msg:
                    current_msg += "```"
                    msgs.append(current_msg)
                
                for msg in msgs:
                    await ctx.send(msg)
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
