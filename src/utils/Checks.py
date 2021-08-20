import discord
import logging
import math
import re

from discord.ext import commands
from src.constants.contants import OWNER_ID

logger = logging.getLogger('__main__.' + __name__)

class No_Owner(commands.CommandError): pass
class No_Perms(commands.CommandError): pass
class No_Guild(commands.CommandError): pass
class No_Guild_Owner(commands.CommandError): pass
class No_Guild_Owner_Bot(commands.CommandError): pass

class Generic_Error(commands.CommandError):
    """Exception raised generic error in code
    
    Attributes
    -----------
    message: str
        Generic message.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(f'{message}')
    
    def __str__(self):
        return self.message

class Generic_Not_Found(Generic_Error):
    def __init__(self, message):
        super().__init__(message)

def is_owner():
    def predicate(ctx):
        if ctx.author.id in OWNER_ID:
            return True
        raise No_Owner()
    return commands.check(predicate)

def is_owner_server():
    def predicate(ctx):
        if ctx.author.id == ctx.guild.owner_id:
            return True
        raise No_Guild_Owner
    return commands.check(predicate)

def is_owner_server_or_bot():
    def predicate(ctx):
        if ctx.author.id == ctx.guild.owner_id or ctx.author.id in OWNER_ID: 
            return True
        raise No_Guild_Owner_Bot
    return commands.check(predicate)

def has_guild(ctx):
    def predicate(ctx):
        if ctx.guild:
            return True
        raise No_Guild
    return commands.check(predicate)

def help_command(comando: object, prefix: str):
    embed=discord.Embed(
            title='Command: {}'.format(comando.name),
            description=comando.description)
    uso = comando.usage.replace('#',prefix[0])
    exemplos = comando.brief.replace('#',prefix[0])
    embed.add_field(name='**Use:**', value=uso)
    embed.add_field(name='**Examples:**', value=exemplos, inline=False)
    embed.add_field(name='\u200B', value='\u200B', inline=False)
    msg_status = lambda status:'✅ Activated' if status == True  else '❌ Disabled'
    embed.add_field(name='Status', value=msg_status(comando.enabled))
    if (len(comando.aliases)>0):
        aliases = ''.join(f"**{alias}** " for alias in comando.aliases)
        embed.add_field(name='**Alias:**', value=aliases)
    return embed

async def c_error(ctx, error: object):
    """
    Args:
        ctx:    context object
        error (object): object of error
    """
    
    info = False
    message = None
    delay = 5
    if isinstance(error, commands.CommandOnCooldown):
        message = 'Wait {} seconds to use that command again.'.format(math.ceil(error.retry_after))
    elif isinstance(error,commands.InvalidEndOfQuotedStringError):
        message = 'Error, parameter reported invalid.'
        delay = 4
    elif isinstance(error, commands.BadArgument):
        message = error
        delay = 4
    elif isinstance(error, commands.DisabledCommand):
        message = '🛠 Command disabled for maintenance'
        delay = 3
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, No_Guild):
        pass
    elif isinstance(error, (No_Owner, No_Guild_Owner_Bot)):
        message = "Permission denied."
        delay = 2
    elif isinstance(error, commands.MissingRequiredArgument):
        info = True
        if ctx.command.name != 'help':
            p = await ctx.bot.get_prefix(ctx.message)
            h = help_command(ctx.command,p)
            await ctx.send(embed=h)
        return
    elif isinstance(error, Generic_Not_Found):
        message = error.message
    elif  isinstance(error, Generic_Error):
        message = 'Error, try again later.'
        logger.error(f"Error: {str(e)} \nType: {type(error)} \n{ctx.message.content}")
    else:
        message = str(error)
        logger.error(f"Error: {str(error)} \nType: {type(error)} \n{ctx.message.content}")
    if message:
        delt = await ctx.channel.send(message)
        #Info is true not delete message
        if not info:
            await delt.delete(delay=delay)
            await ctx.message.delete(delay=delay)
            if(not isinstance(error, commands.CommandOnCooldown)):
                ctx.command.reset_cooldown(ctx)
