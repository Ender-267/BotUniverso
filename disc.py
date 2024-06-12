import discord
from discord.ext import commands, tasks
import json
from sys import argv
import sqlite3
from asyncio import sleep

intents = discord.Intents.default()
intents.message_content = True

ID_CANAL_TOKEN: int = 1246869970340806686
TOKEN_TXT = './token.json'
BASE_DATOS = './base.db'

bot = commands.Bot(command_prefix='!', intents=intents)

def querry_con_handling(cur: sqlite3.Cursor,querry: str, tupla: tuple = ()):
    try:
        cur.execute(querry, tupla)
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            sleep(2)
            return querry_con_handling(cur)
        else:
            raise
    return cur

@tasks.loop(seconds=2)
async def comprobar_validez_token():
    global mandar_mensage
    with open(TOKEN_TXT, 'r') as archivo:
        datos = json.load(archivo)
    if datos["http_error"] and mandar_mensage:
        canal = bot.get_channel(ID_CANAL_TOKEN)
        if canal:
            await canal.send('Inserte token!!')
            mandar_mensage = False

@bot.command(name='token')
async def set_token(ctx, value: str):
    global mandar_mensage
    with open(TOKEN_TXT, 'w') as archivo:
        jsond = {
            "http_error": False,
            "token": value
        }
        json.dump(jsond, archivo)
        mandar_mensage = True
    await ctx.send(f'Token se ha actualizado a: {value}')

@bot.command(name='nick')
async def nick(ctx, value: str):
    try:
        db = sqlite3.connect(BASE_DATOS)
        cur = db.cursor()
        querry = "SELECT contra, ip FROM usuarios NATURAL JOIN datos WHERE usuario = ?"
        tupla = (value,)
        cur = querry_con_handling(cur, querry, tupla)
        
        rows = cur.fetchall()
        if rows:
            msg = "\n".join([f"contra: {row[0]}, ip: {row[1]}" for row in rows])
        else:
            msg = "No se encontraron resultados"
        
        await ctx.send(msg)
    except sqlite3.Error as e:
        await ctx.send(f"Error de sql: {e}")
    finally:
        db.close()



@bot.event
async def on_ready():
    print(f'Logueado como {bot.user}')
    comprobar_validez_token.start()


if __name__ == '__main__':
    token_bot = argv[1]
    mandar_mensage = True
    bot.run(token_bot)
