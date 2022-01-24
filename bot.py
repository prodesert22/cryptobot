import asyncio
import configparser
import discord
import logging
import os
import sys

from discord.ext import commands
from datetime import datetime

from src.utils import Checks
from src.utils.Func_Coin import PATH_SRC

DEFAULT_PREFIX = '#'

# Load config
config = configparser.ConfigParser()
config.read("config.ini")
bot_token = config["Token"]["token"]
log_level = config["Log"]["level"]
if (not bot_token):
    print("No bot Token, add in config.ini")
    sys.exit(0)

intents = discord.Intents.all()
bot = commands.Bot(case_insensitive=True, command_prefix=DEFAULT_PREFIX, intents=intents)
bot.remove_command('help')

date = datetime.now()
PATH_LOGS = os.path.join(PATH_SRC, 'logs')

logger = logging.getLogger()
logger.setLevel(log_level)
handler = logging.FileHandler(
    filename=f'{os.path.join(PATH_LOGS, str(date))}.log', 
    encoding='utf-8', 
    mode='w',
)
handler.setLevel(log_level)
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler) 

@bot.check
def guild(ctx):
    if ctx.guild:
        return True
    raise Checks.No_Guild

@bot.event
async def on_ready():
    print(f"{bot.user.name}, Bot online")
    game = discord.Game("#help")
    await bot.change_presence(status=discord.Status.online, activity=game)
    logger.info(f"{bot.user.name}, Bot online")

@bot.event
async def on_command_error(ctx,error):
    await Checks.c_error(ctx,error)

for filename in os.listdir('./src/commands'):
    try:
        if filename.endswith('.py'):
            bot.load_extension(f'src.commands.{filename[:-3]}')
    except Exception as e:
        logging.warning(f'{filename} raise error. \n{e}')
        continue

bot.run(bot_token)
