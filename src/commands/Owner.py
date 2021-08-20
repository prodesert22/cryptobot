import asyncio
import discord
import logging
import os

from discord.ext import commands

from src.utils import Checks 
from src.utils.Func_Coin import get_symbols, get_exchanges, PATH_SRC

import src.utils.Checks 
from importlib import reload
reload(src.utils.Checks)

class Owner(commands.Cog):
    """Comandos só acessados por admins"""
    def __init__ (self,bot):
        self.bot = bot
        self.emoji = '🔑'
        self.hidden = True
        self.admin = False
        self.logger = logging.getLogger('__main__.' + __name__)

    def get_emoji(self):
        return self.emoji

    def is_hidden(self):
        return self.hidden

    def is_admin(self):
        return self.admin
    
    @commands.command(name='guilds')
    @Checks.is_owner()
    async def guilds(self, ctx):
        await ctx.send(f'Guilds {len(self.bot.guilds)}.')
    
    @commands.command(name='update_coins')
    @Checks.is_owner()
    async def update_coins(self, ctx):
        get_symbols()
        
    @commands.command(name='update_exchanges')
    @Checks.is_owner()
    async def update_exchanges(self, ctx):
        get_exchanges()
    
    @commands.command()
    @Checks.is_owner()
    async def disable(self, ctx, command: str):
        #Disable command
        comando = bot.get_command(command)
        if comando is not None:
            comando.update(enabled=False)
            await ctx.send('Command, {}, desactivated'.format(comando.name))
            self.logger.info('Command, {}, desactivated'.format(comando.name))
        else:
            await ctx.send('Command, {}, not found.'.format(comando.name))

    @commands.command()
    @Checks.is_owner()
    async def enable(self, ctx, command: str):
        #Active command
        comando = bot.get_command(command)
        if comando is not None:
            comando.update(enabled=True)
            await ctx.send('Command, {}, activated.'.format(comando.name))
            self.logger.info('Command, {}, activated.'.format(comando.name))
        else:
            await ctx.send('Command, {}, not found.'.format(comando.name))

    @commands.command()
    @Checks.is_owner()
    async def load(self, ctx, extension: str):
        try:
            self.bot.load_extension(f'src.commands.{extension.capitalize()}')
            await ctx.send(f'Cog {extension.capitalize()} load.')
            self.logger.info(f'Cog {extension.capitalize()} load.')
        except Exception as e :
            await ctx.send(f'Error in load {extension.capitalize()}.\n{e}')
            self.logger.error(e)

    @commands.command()
    @Checks.is_owner()
    async def unload(self, ctx, extension: str):
        try:
            self.bot.unload_extension(f'src.commands.{extension.capitalize()}')
            await ctx.send(f'Cog {extension.capitalize()} unload.')
            self.logger.info(f'Cog {extension.capitalize()} unload.')
        except Exception as e :
            await ctx.send(f'Error in unload {extension.capitalize()}.\n{e}')
            self.logger.error(e)

    @commands.command(name='reload')
    @Checks.is_owner()
    async def reload_cog(self, ctx, extension: str):
        try:
            self.bot.reload_extension(f'src.commands.{extension.capitalize()}')
            await ctx.send(f'Cog {extension.capitalize()} reload.')
            self.logger.info(f'Cog {extension.capitalize()} reload.')
        except Exception as e :
            await ctx.send(f'Error in reload {extension.capitalize()}. \n{e}')
            self.logger.error(e)

    @commands.command(name='reload_all')
    @Checks.is_owner()
    async def reload_cog_all(self, ctx):
        try:
            for filename in os.listdir(os.path.join(PATH_SRC, 'commands')):
                if filename.endswith('.py'):
                    self.bot.reload_extension(f'src.commands.{filename[:-3]}')
            await ctx.send('All cogs reloaded.')
            self.logger.info("Reload all cogs")
        except Exception as e:
            await ctx.send(f'Error in reload all. \n{e}')
            self.logger.error(e)
    
def setup(bot):
    bot.add_cog(Owner(bot))
