import asyncio
import discord
import logging
from discord.ext import commands, tasks

from src.utils.Func_Coin import current_price, format_tostring_value
from src.utils.Checks import Generic_Error

class Status(commands.Cog):
    def __init__ (self,bot):
        self.bot = bot
        self.emoji = '❓'
        self.hidden = True
        self.admin = False
        self.logger = logging.getLogger('__main__.' + __name__)
        self.symbols = ['#help','BTC','ETH','BNB','AVAX']
        self.index = 0
        self.change_status.start()
        
    def get_emoji(self):
        return self.emoji

    def is_hidden(self):
        return self.hidden

    def is_admin(self):
        return self.admin
    
    def cog_unload(self):
        self.change_status.cancel()

    @tasks.loop(seconds=15.0)
    async def change_status(self):
        error = None
        if (self.index == 0):
            game = discord.Game("#help")
            self.index +=1
        else:
            try:
                price = await current_price(self.symbols[self.index], 'USDT')
            except Exception as e:
                price = 0
                self.logger.error(str(e))
            str_price = format_tostring_value(price)
            game = discord.Game(f'{self.symbols[self.index]} - ${str_price}')
            if self.index == len(self.symbols)-1:
                self.index = 0
            else:
                self.index +=1
        await self.bot.change_presence(status=discord.Status.online, activity=game)

    @change_status.before_loop
    async def before_printer(self):
        print('waiting...')
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Status(bot))
