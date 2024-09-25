import discord
from discord.ext import commands, tasks
import json
import sqlite3
import asyncio
import hashlib
import os
from prettytable import PrettyTable
from typing import List, Tuple

# Constants
ID_CANAL_TOKEN = 1246869970340806686
TOKEN_FILE = './token.json'
MAIN_DB = './base_v3.db'
PLOTS_DB = '../ModTest/plots.db'
MESSAGE_BUFFER_DIR = './message_buffer'

# Ensure message buffer directory exists
os.makedirs(MESSAGE_BUFFER_DIR, exist_ok=True)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global variable to manage token message
should_send_message = True

async def execute_query(cur: sqlite3.Cursor, query: str, params: tuple = ()) -> sqlite3.Cursor:
    """Execute an SQLite query with error handling and retries."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            cur.execute(query, params)
            cur.connection.commit()
            return cur
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

def create_table_file(headers: List[str], rows: List[Tuple]) -> str:
    """Create a formatted table file and return its path."""
    table = PrettyTable()
    table.field_names = headers
    table.align = 'l'
    for row in rows:
        table.add_row(row)
    
    table_str = table.get_string()
    file_hash = hashlib.md5(table_str.encode()).hexdigest()
    file_path = os.path.join(MESSAGE_BUFFER_DIR, f"{file_hash}.txt")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(table_str)
    
    return file_path

@tasks.loop(seconds=2)
async def check_token_validity():
    global should_send_message
    with open(TOKEN_FILE, 'r') as file:
        data = json.load(file)
    if data.get("http_error") and should_send_message:
        channel = bot.get_channel(ID_CANAL_TOKEN)
        if channel:
            await channel.send('Insert token!!')
            should_send_message = False

async def set_token_helper(ip: str, value: str) -> str:
    global should_send_message
    MAX_HEADER = 2
    try:
        ip = int(ip)
        if not 0 <= ip <= MAX_HEADER:
            return 'Error: Invalid header ID'
    except ValueError:
        return 'Error: Invalid header ID'

    with open(TOKEN_FILE, 'w') as file:
        json_data = {
            "http_error": False,
            "token": value,
            "header_id": ip
        }
        json.dump(json_data, file)
        should_send_message = True
    return f'Token has been updated to: {value}'

async def search_database(ctx, value: str, query: str, db_path: str):
    value = value.lower()
    try:
        with sqlite3.connect(db_path) as db:
            cur = db.cursor()
            await execute_query(cur, query, (value,))
            rows = cur.fetchall()
            if rows:
                headers = [description[0] for description in cur.description]
                file_path = create_table_file(headers, rows)
                await ctx.send(file=discord.File(file_path))
                os.remove(file_path)
            else:
                await ctx.send("No results found")
    except sqlite3.Error as e:
        await ctx.send(f"SQL Error: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()
    check_token_validity.start()

@bot.tree.command(name='token', description='Set a new token')
async def set_token(interaction: discord.Interaction, ip: str, value: str):
    response = await set_token_helper(ip, value)
    await interaction.response.send_message(response)

@bot.tree.command(name='nick', description='Search nicks')
async def search_nick(interaction: discord.Interaction, value: str):
    query = "SELECT usuario, contra, ip, db_proveniente, tipo_contra FROM usuarios NATURAL JOIN datos WHERE usuario GLOB ? ORDER BY usuario LIMIT 100000"
    await search_database(interaction, value, query, MAIN_DB)

@bot.tree.command(name='ip', description='Search by IP')
async def search_ip(interaction: discord.Interaction, value: str):
    query = "SELECT usuario, contra, ip, db_proveniente, tipo_contra FROM usuarios NATURAL JOIN datos WHERE ip GLOB ? ORDER BY ip LIMIT 100000"
    await search_database(interaction, value, query, MAIN_DB)

@bot.tree.command(name='pass', description='Search by password')
async def search_pass(interaction: discord.Interaction, value: str):
    query = "SELECT usuario, contra, ip, db_proveniente, tipo_contra FROM usuarios NATURAL JOIN datos WHERE contra GLOB ? ORDER BY contra LIMIT 100000"
    await search_database(interaction, value, query, MAIN_DB)

@bot.tree.command(name='plot', description='Search plot information')
async def search_plot(interaction: discord.Interaction, value: str):
    query = "SELECT plot_x, plot_y, dueño, tipo_relacion FROM plots NATURAL JOIN pertenece_a_plot WHERE LOWER(usuario) = ? AND tipo_relacion != 'DENY'"
    await search_database(interaction, value, query, PLOTS_DB)

async def search_database(interaction: discord.Interaction, value: str, query: str, db_path: str):
    value = value.lower()
    try:
        with sqlite3.connect(db_path) as db:
            cur = db.cursor()
            await execute_query(cur, query, (value,))
            rows = cur.fetchall()
            if rows:
                headers = [description[0] for description in cur.description]
                file_path = create_table_file(headers, rows)
                await interaction.response.send_message(file=discord.File(file_path))
                os.remove(file_path)
            else:
                await interaction.response.send_message("No results found")
    except sqlite3.Error as e:
        await interaction.response.send_message(f"SQL Error: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"An error occurred: {str(error)}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python filename.py <TOKEN>")
    else:
        bot_token = sys.argv[1]
        bot.run(bot_token)