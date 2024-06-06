import discord
from discord.ext import commands, tasks
import json
from sys import argv

intents = discord.Intents.default()
intents.message_content = True

ID_CANAL: int = 1246869970340806686
TOKEN_TXT = './token.json'

bot = commands.Bot(command_prefix='!', intents=intents)

@tasks.loop(seconds=2)
async def monitor_global_variable():
    global mandar_mensage
    with open(TOKEN_TXT, 'r') as archivo:
        datos = json.load(archivo)
    if datos["http_error"] and mandar_mensage:
        canal = bot.get_channel(ID_CANAL)
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

@bot.event
async def on_ready():
    print(f'Logueado como {bot.user}')
    monitor_global_variable.start()


if __name__ == '__main__':
    token_bot = argv[1]
    mandar_mensage = True
    bot.run(token_bot)
