import discord
import logging
import sys
import os

from discord.ext import commands

from src.constants.contants import OWNER_ID
from src.utils.Checks import Generic_Not_Found, help_command

def is_admin_owner(ctx):
    return ctx.author.id in OWNER_ID or ctx.guild.owner_id == ctx.author.id

class Help(commands.Cog):
    def __init__ (self,bot):
        self.bot = bot
        self.emoji = '❓'
        self.hidden = True
        self.admin = False
        self.logger = logging.getLogger('__main__.' + __name__)

    def get_emoji(self):
        return self.emoji

    def is_hidden(self):
        return self.hidden

    def is_admin(self):
        return self.admin

    @commands.command(name='help',aliases=['command'])
    @commands.cooldown(1,5, commands.BucketType.user)
    async def comandos(self, ctx, command_name: str):
        comando = self.bot.get_command(command_name)
        found = False
        if comando is not None:
            cog = comando.cog
            #not take the command that is not in a cog
            if (
                cog is not None 
                and ( (cog.is_admin() is True and is_admin_owner(ctx) is True) 
                or cog.is_hidden() is False )
            ):
                found = True
        if found:
            p = await self.bot.get_prefix(ctx.message)
            h = help_command(comando, p)
            await ctx.send(embed=h)
            return
        raise Generic_Not_Found('Command not found.')
            
    @comandos.error
    async def comandos_error(self,ctx,error):
        if isinstance(error, commands.MissingRequiredArgument):
            p = await self.bot.get_prefix(ctx.message)
            h=discord.Embed(
                title='All bot commands by categories.',
                description='Use `{}help <command>` to learn more about this command'.format(p[0]))
            for nome in self.bot.cogs:
                c_ext = self.bot.cogs[nome]
                if(c_ext.is_hidden() is True and not ctx.author.id in OWNER_ID):
                    if c_ext.is_admin() is False or is_admin_owner(ctx) is False:
                        continue
                comandos = ''
                for c in c_ext.walk_commands():
                    comandos += "__**{}**__ ".format(c) 
                if(comandos != ''):
                    h.add_field(name="{} **{}**".format(c_ext.get_emoji(),nome),value=comandos,inline=True)
            await ctx.send(embed=h)
        else:
            pass

def setup(bot):
    bot.add_cog(Help(bot))
