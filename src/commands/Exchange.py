import asyncio
import discord
import logging
import os

from datetime import datetime
from discord.ext import commands
from src.utils.Func_Coin  import exchange_info 

import src.utils.Func_Coin 
from importlib import reload
reload(src.utils.Func_Coin)

class Exchange(commands.Cog, name="Exchanges"):
    """Comandos só acessados por admins"""
    def __init__ (self,bot):
        self.bot = bot
        self.emoji = '🔑'
        self.hidden = False
        self.admin = False
        self.logger = logging.getLogger('__main__.' + __name__)

    def get_emoji(self):
        return self.emoji

    def is_hidden(self):
        return self.hidden

    def is_admin(self):
        return self.admin
        
    @commands.command(name='exchangeinfo', aliases=['infoex'],
    usage='#exchangeinfo <exchange> ',
    description='Informations for a exchange',
    brief='#exchangeinfo binance')
    @commands.cooldown(1,10, commands.BucketType.user)
    async def exchangeinfo(self,ctx, exchange: str):
        dic = await exchange_info(exchange)
        centralized = lambda var : 'Centralized' if bool(var) is True else 'Decentralized'
        emb = discord.Embed(title = f"{dic['name']} exchange information:",
                description = centralized(dic['centralized']),
                timestamp= datetime.utcnow(),
                url= f"{dic['site']}",
                colour = 0)
        emb.set_thumbnail(url=dic['logo'])
        info_str = ''
        info_str += "Trade volume in 24h in btc: **{}**\n".format(dic['trade_volume_24h_btc'])
        info_str += "Trade volume in 24h in usd: **${}**\n".format(dic['trade_volume_24h_usd'])
        emb.add_field(name='Infos', value=info_str,inline=False)
        emb.add_field(name='release: {}'.format(dic['release']), value='\u200b')
        link = ''
        if(dic['site']):
            link += '[Site]({})\n'.format(dic['site'])
        if(dic['twitter']):
            link += '[Twitter]({})\n'.format(dic['twitter'])
        if(dic['reddit']):
            link += '[Reddit]({})\n'.format(dic['reddit'])
        if(dic['telegram']):
            link += '[Chat]({})\n'.format(dic['telegram'])
        if(dic['facebook']):
            link += '[facebook]({})\n'.format(dic['facebook'])
        emb.add_field(name='Links', value=link, inline=False)
        emb.set_footer(
            text='Powered by coingecko', 
            icon_url='https://static.coingecko.com/s/thumbnail-007177f3eca19695592f0b8b0eabbdae282b54154e1be912285c9034ea6cbaf2.png',
        )
        await ctx.send(embed=emb)
        
def setup(bot):
    bot.add_cog(Exchange(bot))
