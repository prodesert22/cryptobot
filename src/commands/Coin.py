import asyncio
import discord
import logging

from discord.ext import commands
from datetime import datetime
from io import BytesIO
from typing import Union

import src.utils.Func_Coin # pylint: disable=import-error
from importlib import reload
reload(src.utils.Func_Coin)

from src.utils.Func_Coin import (
    chart,
    coin_info,
    convert_price,
    current_price,
    format_tostring_value,
    get_crypto_logo,
    get_exchange_logo,
    get_ohlc_binance,
    get_crypto_exchanges,
    price_exchange,
) 
from src.utils.Converts import Convert_Timeframes, Convert_to_Timeframes, Timeframe

class Coin(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self.emoji = '🪙'
        self.hidden = False
        self.admin = False
        self.logger = logging.getLogger('__main__.' + __name__)
        
    def get_emoji(self) -> str:
        return self.emoji

    def is_hidden(self) -> bool:
        return self.hidden

    def is_admin(self) -> bool:
        return self.admin

    @commands.command(
        name='chart', 
        aliases=['graphic'],
        usage=f'#chart <symbol> <symbol pair>[USDT] <interval candle>[default 1h]'
        f'<max candle>[max 1k]',
        description=f'Create a chart for interval in candle (Binance)'
        f'\n Intervals supported: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 3d, 1w, 1M.',
        brief='#chart btc 1d \n#chart eth btc 30m\n #chart eth btc 30m 100 \n #chart avax 100'
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def c_chart(
        self,
        ctx,
        symbol1: str,
        param1: Convert_to_Timeframes = Timeframe("1h"),
        param2: Convert_Timeframes = Timeframe("1h"),
        limit: int = None,
    ) -> None:
        if isinstance(param1, Timeframe):
            symbol2 = 'USDT'
            interval = param1
            if isinstance(param2, int):
                limit = param2
        elif isinstance(param1, int):
            limit = param1
            symbol2 = 'USDT'
            interval = param2
        else:
            symbol2 = param1
            if isinstance(param2, int):
                limit = param2
                interval = Timeframe("1h")
            else:
                interval = param2

        candles = await get_ohlc_binance(symbol1.upper(), symbol2.upper(), interval, limit)
        img = await chart(
            symbol1=symbol1.upper(),
            symbol2=symbol2.upper(),
            candles=candles,
            interval=str(interval),
        )
        emb = discord.Embed(
            title = f"{symbol1.upper()}/{symbol2.upper()} interval {str(interval)}",
            description = "",
            timestamp = datetime.utcnow(),
            url=f"https://www.binance.com/en/trade/{symbol1}_{symbol2}?type=spot",
            colour = 180342 if candles['open'][-1] <= candles['close'][-1] else 16271712
        )
        emb.add_field(
            name='Current price', 
            value=format_tostring_value(candles['close'][-1]), 
            inline=True,
        )
        emb.add_field(
            name='High in period', 
            value=format_tostring_value(max(candles['high'])), 
            inline=True,
        )
        emb.add_field(
            name='Low in period', 
            value=format_tostring_value(min(candles['low'])), 
            inline=True,
        )
        file = discord.File(fp=img, filename='chart.png')
        emb.set_image(url="attachment://chart.png")
        number = len(candles['dates'])
        emb.set_footer(
            text=f'Powered by binance || {number} candles', 
            icon_url='https://user-images.githubusercontent.com/12424618/54043975-b6cdb800-4182-11e9-83bd-0cd2eb757c6e.png'
            )
        await ctx.send(embed=emb, file=file)
    
    @commands.command(
        name='coininfo', 
        aliases=['infocoin,tokeninfo,infotoken'],
        usage='#coininfo <symbol> ',
        description='Informations for a coin',
        brief='#coininfo btc'
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def coininfo(self, ctx, symbol: str) -> None:
        dic = await coin_info(symbol)
        emb = discord.Embed(
            title = f"{dic['name']} information:",
            description = "**{}**".format(symbol.upper()),
            timestamp= datetime.utcnow(),
            url= f"https://www.coingecko.com/en/coins/{dic['coin_id']}",
            colour = 0
        )
        emb.set_thumbnail(url=dic['logo'])
        info_str = 'Rank: **{}**\n'.format(dic['rank'])
        market_cap = dic['market_cap']
        circulating_supply = dic['circulating_supply']
        max_supply = dic['max_supply']
        total_supply =dic['total_supply']
        info_str += "Market Cap: **${}**\n".format(market_cap)
        info_str += "Circulation Supply: **{}**\n".format(circulating_supply)
        info_str += "Total Supply: **{}**\n".format(total_supply)  
        info_str += "Max Supply: **{}**\n".format(max_supply) 
        emb.add_field(name='Infos', value=info_str,inline=False)
        emb.add_field(name='Current price:', value='**{}**'.format(dic['current_price']))
        emb.add_field(name='ATH:', value='**{}**'.format(dic['ath']))
        emb.add_field(name='ATL:', value='**{}**'.format(dic['atl']))
        link = ''
        if(dic['site']):
            link += '[Site]({})\n'.format(dic['site'])
        if(dic['twitter']):
            link += '[Twitter]({})\n'.format(dic['twitter'])
        if(dic['reddit']):
            link += '[Reddit]({})\n'.format(dic['reddit'])
        if(dic['chat']):
            link += '[Chat]({})\n'.format(dic['chat'])
        if(dic['explorer']):
            link += '[Blockchain Explorer]({})\n'.format(dic['explorer'])
        if(dic['code']):
            link += '[Source Code]({})\n'.format(dic['code'])
        emb.add_field(name='Links', value=link, inline=False)
        emb.set_footer(
            text='Powered by coingecko', 
            icon_url='https://static.coingecko.com/s/thumbnail-007177f3eca19695592f0b8b0eabbdae282b54154e1be912285c9034ea6cbaf2.png'
        )
        await ctx.send(embed=emb)
        
    @commands.command(
        name='crypto', 
        aliases=['price,coin'],
        usage='#crypto <symbol> <symbol2>[USD] <exchange>[default binance]',
        description='Get price in USD, volume, high, low for coin in exchange.',
        brief='#crypto btc'
    )
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def crypto(
        self, 
        ctx, 
        symbol1: str, 
        symbol2: str = 'USDT', 
        exchange: str ='binance',
    ) -> None:
        dic = price_exchange(exchange, symbol1, symbol2)
        emb = discord.Embed(title = "**{}/USD**".format(symbol1.upper()),
                description = "Price: **{}**".format(dic['price']),
                timestamp= datetime.utcfromtimestamp(dic['timestamp']/1000),
                colour = discord.Color.blue())
        info_str = 'High: **{}**\n'.format(dic['high'])
        info_str += 'Low: **{}**\n'.format(dic['low'])
        info_str += 'Volume in {}: **{}**\n'.format(symbol1.upper(),dic['volume_symbol'])
        info_str += 'Volume in USD: **{}**\n'.format(dic['volume'])
        info_str += 'Change in USD: **{}**\n'.format(dic['change'])
        info_str += 'Percentage change: **{}%**\n'.format(dic['percentage'])
        emb.add_field(name='24h Market Data', value=info_str,inline=False)
        emb.set_footer(text='Exchange: {}'.format(exchange.lower()))
        logo = await get_crypto_logo(symbol1)
        if(logo):
            emb.set_thumbnail(url=logo)
        exchange_logo = await get_exchange_logo(exchange)
        if(exchange_logo):
            emb.set_footer(
                text='Exchange: {}'.format(exchange.lower()), 
                icon_url=exchange_logo
            )
        await ctx.send(embed=emb)

    @commands.command(
        name='exchange', 
        aliases=['listexchange'],
        usage='#exchange <symbol>',
        description='Returns an exchange list where the token is listed',
        brief='#exchange btc'
    )
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def cryptoinfoexchanges(self, ctx, symbol: str) -> None:
        tickers = await get_crypto_exchanges(symbol)
        list_crypto_exchanges = tickers['list_crypto_exchanges']
        name = tickers['name']
        logo = tickers['logo']
        id_symbol = tickers['id_symbol']
        pags = list()
        #TODO mudar para buttons https://pypi.org/project/discord-components/ e causar exception de tempo de mais na reacao 
        if(list_crypto_exchanges):
            emb_pag = discord.Embed(title = f"**Exchanges where {name} is listed**",
                description = f"**[{symbol.upper()}](https://www.coingecko.com/en/coins/{id_symbol})**",
                colour = discord.Color.blue())
            emb_pag.set_thumbnail(url=logo)
            default = emb_pag.copy()
            for cont, ticker  in enumerate(list_crypto_exchanges):
                cont +=1
                emb_pag.add_field(
                    name = f'Exchange {ticker.exchange}: {symbol.upper()}/{ticker.pair}',
                    value = f'**Price: ${ticker.value}\n'
                    f'Volume : ${ticker.volume_usd}\n'
                    f'[Trade]({ticker.url})**',
                    inline = False,
                )
                if (cont % 5 == 0) or (cont == len(list_crypto_exchanges)):
                    pags.append(emb_pag)
                    emb_pag = default.copy()
            for num in range(len(pags)):
                pags[num].set_footer(text='{}/{}'.format(num+1,len(pags)))
            id_pag = 0
            menssagem = await ctx.send(embed=pags[id_pag])
            await menssagem.add_reaction('⬅️')
            await menssagem.add_reaction('➡️')
            while True:
                def check(reaction, user):
                    return reaction.message.id == menssagem.id and (str(reaction.emoji) == '⬅️' or str(reaction.emoji) == '➡️') and not user.bot == True
                try:
                    r = await self.bot.wait_for('reaction_add', check=check, timeout=10)
                    if(str(r[0].emoji) == '⬅️' and not id_pag == 0):
                        id_pag -= 1
                        emb = pags[id_pag]
                        await menssagem.remove_reaction('⬅️', ctx.message.author)
                        await menssagem.edit(embed=emb)
                    if(str(r[0].emoji) == '➡️' and not id_pag == len(pags)-1):
                        id_pag += 1
                        emb = pags[id_pag]
                        await menssagem.remove_reaction('➡️', ctx.message.author)
                        await menssagem.edit(embed=emb)
                except asyncio.TimeoutError:
                    break
            
    @commands.command(
        name='convert', 
        aliases=['trade'],
        usage='#convert <symbol/amount> <symbol/amount>[default usd] <symbol/amount>[default 1]',
        description='Returns an exchange list where the token is listed',
        brief='#convert btc\n#convert avax btc\n#convert avax usd 100'
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def convert(
        self, 
        ctx, 
        param1: Union[float, str], 
        param2: Union[float, str] = 'usd', 
        param3: Union[float, str] = 1,
    ) -> None:
        if isinstance(param1, float):
            symbol = param2.lower()
            amount = abs(param1)
            symbol2 = param3.lower() if isinstance(param3, str) else 'usd'
        elif isinstance(param2, float):
            symbol = param1.lower()
            amount = abs(param2)
            symbol2 = param3.lower() if isinstance(param3, str) else 'usd'
        else:
            symbol = param1.lower() if isinstance(param1, str) else 'usd'
            symbol2 = param2.lower() if isinstance(param2, str) else 'usd'
            if isinstance(param3, float):
                amount = abs(param3)
            else:
                raise commands.BadArgument('Amount is invalid')

        convert_amount = await convert_price(symbol, symbol2, amount)
        await ctx.send(f'{amount} {symbol} equal {convert_amount} {symbol2}')
        
def setup(bot):
    bot.add_cog(Coin(bot))
