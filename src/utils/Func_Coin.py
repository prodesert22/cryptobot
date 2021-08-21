import asyncio
import aiohttp
import ccxt
import json
import os
import requests

from aiohttp.client_reqrep import ClientResponse
from ccxt.base.errors import BadSymbol
from datetime import datetime
from decimal import Decimal
from discord.ext.commands import BadArgument
from io import BytesIO
from json.decoder import JSONDecodeError
import plotly.graph_objects as go
from typing import Optional, List, Dict, Any, Union

from .Checks import Generic_Error, Generic_Not_Found
from .Converts import Timeframe

PATH_ABS = os.path.abspath(".")
PATH_SRC = os.path.join(PATH_ABS,'src')
PATH_DATA = os.path.join(PATH_SRC,'Data')
TIMEOUT = 30

def get_value_json(file: str, key: str) -> Optional[str]:
    try:
        path_file = os.path.join(PATH_DATA, file)
        with open(path_file) as file:
                data = json.load(file)
        return data[key]
    except KeyError:
        return None

def format_tostring_value(value: Union[int, float, str, Decimal]) -> str:
    """Format number

    Args:
        value (Union[int, float, str, Decimal])

    Returns:
        str
    """
    
    try:
        value = float(value)
    except Exception:
        return 'None'
    return '{0:,}'.format(value)

class aiohttp_reponse:
    def __init__(
        self,
        status: int,
        json: dict,
        text: str,
        url: str,
    ) -> None:
        self.status = status
        self.atr_json = json
        self.text = text
        self.url = url
        
    def json(self) -> Dict[str, Any]:
        return self.atr_json

async def fetch(
    url: str, 
    params: Dict[str, Any] = None, 
    timeout: int = TIMEOUT,
    pass_statuscode: bool = False,
) -> aiohttp_reponse:
    """Request Get

    Args:
        url (str): url of the api
        params (Dict[str, Any], optional): parameters. Defaults to None.
        timeout (int, optional): delay of timeout in seconds. Defaults to TIMEOUT.
        pass_statuscode (bool, optional): bool to pass status code different from 200. Defaults to False.

    Raises:
        Generic_Error: raise generic errors

    Returns:
        aiohttp_reponse: [description]
    """
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=timeout) as r:
                if r.status != 200 and not pass_statuscode:
                    raise Generic_Error(f'Error - status code: {r.status}\n Url: {r.url}')
                response = aiohttp_reponse(r.status, await r.json(), r.text, r.url)
    except asyncio.exceptions.TimeoutError:
        raise Generic_Error(f"Timeout error in request. Url: {url}.")
    except JSONDecodeError:
        raise Generic_Error(
            f"Request {response.url} returned invalid"
            f'JSON response: {response.text}',
        ) from e
    except Exception as e:
        raise Generic_Error(f"Error in fetch: {e}") from e
    return response

async def get_ohlc_binance(
    symbol1: str, 
    symbol2: str, 
    interval: Timeframe, 
    limit: int = None,
) -> Dict[str, Any]:
    """Get Candles from the binance

    Args:
        symbol1 (str): symbol1 is the symbol  of the coin/token regarding symbol2
        symbol2 (str): symbol2 is the symbol of the coin/token that will be paired in symbol1
        interval (Timeframe): is the size of candle in time
        limit (int, optional): is total of candles. Defaults to None.

    Raises:
        Generic_Not_Found: raise in not found symbol.
        Generic_Error: raise in errors.
        BadArgument: raise in passed the maximum limit of 1000 candles
    Returns:
        Dict{
            dates: list[int], #timestamp
            open  list[Decimal],
            high  list[Decimal],
            low  list[Decimal],
            close  list[Decimal],
        }
    """
    
    if symbol2 == 'USD':
        symbol2 = 'USDT'
    if limit is None:
        limit = interval.limit
    elif limit > 1000:
        raise BadArgument("Passed the maximum limit of 1000 candles.")
    params = {
        "symbol": f"{symbol1}{symbol2}",
        "interval": interval.timeframe,
        "limit": limit,
    }
    response = await fetch(
        url = f'https://api.binance.com/api/v3/klines', 
        params = params, 
        pass_statuscode = True,
    )
    if(response.status == 200):
        candles = {
            'dates': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
        }
        for candle in response.json():
            candles['dates'].append(datetime.utcfromtimestamp(candle[0]/1000))
            candles['open'].append(Decimal(str(candle[1])))
            candles['high'].append(Decimal(str(candle[2])))
            candles['low'].append(Decimal(str(candle[3])))
            candles['close'].append(Decimal(str(candle[4])))
        return candles
    else:
        error = response.json()
        if(error['msg'] == 'Invalid symbol.'):
            raise Generic_Not_Found(f'Not found pair {symbol1}/{symbol2} in binance.')
        else:
            raise Generic_Error(error['msg'])

async def chart(
    symbol1: str, 
    symbol2: str, 
    candles: Dict[str, List], 
    interval: str,
) -> BytesIO:
    """Generate image of candle stick chart

    Args:
        symbol1 (str): symbol1 is the symbol  of the coin/token regarding symbol2
        symbol2 (str): symbol2 is the symbol of the coin/token that will be paired in symbol1
        candles (Dict[str, List]): Dict of close value list, open, low, high and dates in timestamp
        interval (Timeframe): interval of candles #15m, 1h, 12h, 1d ...

    Returns:
        BytesIO: return image in BytesIO object
    """
    
    data = go.Candlestick(
        x=candles['dates'], 
        open=candles['open'], 
        high=candles['high'],
        low=candles['low'], 
        close=candles['close'],
        increasing_line_color='#02C076', decreasing_line_color='#F84960')
    layout = go.Layout(
        paper_bgcolor='#191B20',
        plot_bgcolor='#191B20',
        title = dict(
            text=f'{symbol1}/{symbol2} Interval {interval}',
            x=0.5,
            font = dict(
                size=47,
                color ='#FFFFFF'
            )
        ),
        yaxis = dict(
            title='Price', 
            titlefont=dict(size=40),
            color='#FFFFFF',
            tickfont=dict(size=25),
            gridwidth=1, 
            gridcolor='#2B3139'
        ),
        xaxis = dict(
            title='Date', 
            titlefont=dict(size=40),
            color ='#FFFFFF',
            tickfont=dict(size=25),
            gridwidth=1, 
            gridcolor='#2B3139',
            rangeslider=dict(visible=False)
        ),
    )
    fig = go.Figure(data=data, layout = layout)
    color = '#02C076' if candles['open'][-1] <= candles['close'][-1] else '#F84960'
    fig.add_hline(y=float(candles['close'][-1]), line_width=1, line_dash="dash", line_color=color)
    fig.update_layout(margin=dict(r=150))
    fig.add_annotation(dict(
        font=dict(color="#FFFFFF",size=25),
        x=1.045,
        y=candles['close'][-1],
        text=format_tostring_value(candles['close'][-1]),
        xref="paper",
        yref="y",
        bgcolor=color,
        xanchor='center',
        showarrow=False      
    ))
    
    #Save to BytesIO object
    img_bytes= fig.to_image(format="png", width=1920, height=1080, engine="kaleido")
    img_byteio = BytesIO(img_bytes)
    img_byteio.seek(0)
    return img_byteio

def price_exchange(exchange: str, symbol1: str, symbol2: str) -> Dict[str, Any]:
    """Get price for symbom in specified exchange

    Args:
        exchange (str): binance, coibase...
        symbol1 (str): symbol for coin/token
        symbol2 (str): symbol for coin/token

    Raises:
        Generic_Not_Found: raise in not found exchange or symbol
        Generic_Error: raise case not key in return on ccxt

    Returns:
        Dict[str, Any]
    """
    exchange = exchange.lower()
    symbol1 = symbol1.upper()
    symbol2 = symbol2.upper()
    try:
        exchange_class = getattr(ccxt, exchange)
        exchange = exchange_class()
        ticker = exchange.fetch_ticker(f'{symbol1}/{symbol2}')
        price = (Decimal(ticker['ask']) + Decimal(ticker['bid'])) / 2
        price = format_tostring_value(price)
        format_value = lambda c: float(c) if c is not None else 0
        change = format_value(ticker['change'])
        change = format_tostring_value(change)
        percentage = format_value(ticker['percentage'])
        percentage = format_tostring_value(percentage)
        timestamp =  ticker['timestamp']
        volume_symbol = format_value(ticker['baseVolume'])
        volume_symbol = format_tostring_value(volume_symbol)
        volume = format_value(ticker['quoteVolume'])
        volume = format_tostring_value(volume)
        low = format_value(ticker['low'])
        low = format_tostring_value(low)
        high = format_value(ticker['high'])
        high = format_tostring_value(high)
        return {
            'price': price,
            'change': change,
            'percentage': percentage,
            'timestamp': timestamp,
            'volume_symbol': volume_symbol,
            'volume': volume,
            'low': low,
            'high': high
        }
    except AttributeError as e:
        raise Generic_Not_Found(f'Not found exchange: {exchange}') from e
    except BadSymbol as e:
        raise Generic_Not_Found(e) from e
    except KeyError as e:
        raise Generic_Error(e)

async def current_price(symbol1: str, symbol2: str) -> Decimal:
    symbol1 = symbol1.upper()
    symbol2 = symbol2.upper()
    params = {
        "symbol": f"{symbol1}{symbol2}"
    }
    response = await fetch(
        url = f'https://api.binance.com/api/v3/ticker/price', 
        params = params, 
        pass_statuscode = True,
    )
    if(response.status == 200):
        price = response.json()
        return Decimal(price['price'])
    elif(response.status == 400):
        raise Generic_Not_Found(error['msg'] )
    raise Generic_Error(f'Error - status code: {response.status}')

async def convert_price(from_symbol: str, to_symbol: str, amount: float) -> str:
    """Convert coin/token in other coin/token 

    Args:
        from_symbol (str)
        to_symbol (str)
        amount (float)

    Returns:
        Decimal
    """
    coin_id = get_value_json('Symbol_id.json', from_symbol.upper())
    if(coin_id is None):
        raise Generic_Not_Found(f'Not found symbol {from_symbol}')
    params = {
        "localization": "false",
        "community_data": "false",
        "developer_data": "false",
    }
    response = await fetch(f'https://api.coingecko.com/api/v3/coins/{coin_id}', params)
    info = response.json()
    current_prices = info['market_data']['current_price']
    if to_symbol in current_prices:
        return format_tostring_value(Decimal(str(current_prices[to_symbol]))*Decimal(str(amount)))
    coin_id2 = get_value_json('Symbol_id.json', to_symbol.upper())
    if (coin_id2 is None):
        raise Generic_Not_Found(f'Not found symbol {to_symbol}')
    response2 = await fetch(f'https://api.coingecko.com/api/v3/coins/{coin_id2}', params)
    info2 = response2.json()
    currentp_usd2 = Decimal(info2['market_data']['current_price']['usd'])
    currentp_usd = Decimal(current_prices['usd'])
    try:
        return format_tostring_value((currentp_usd/currentp_usd2)*Decimal(amount))
    except ZeroDivisionError:
        return format_tostring_value(0)

async def coin_info(symbol: str) -> Dict[str, Any]:
    """Return Information of coin/token

    Args:
        symbol (str): symbol of coin/token

    Raises:
        Generic_Not_Found: raise in not found exchange or symbol
        Generic_Error: raise in missing key in dict

    Returns:
        Dict[str, Any]
    """
    
    symbol = symbol.upper()
    coin_id = get_value_json('Symbol_id.json', symbol)
    if(coin_id is None):
        raise Generic_Not_Found(f'Not found symbol {symbol}.')
    params = {
        "localization": "false",
        "community_data": "false",
        "developer_data": "false",
    }
    response = await fetch(f'https://api.coingecko.com/api/v3/coins/{coin_id}', params)
    info = response.json()
    try:
        name = info['name']
        logo = info['image']['large']
        ver = lambda value: value[0] if len(value) > 0 else None
        site = ver(info['links']['homepage'])
        explorer = ver(info['links']['blockchain_site'])
        chat = ver(info['links']['chat_url'])
        if(info['links']['twitter_screen_name'] is not None):
            twitter = 'https://twitter.com/'+info['links']['twitter_screen_name']
        else:
            twitter = None
        if(info['links']['subreddit_url'] is not None):
            reddit = info['links']['subreddit_url']
        else:
            reddit = None
        source_code = ver(info['links']['repos_url']['github'])
        market_cap = format_tostring_value(info['market_data']['market_cap']['usd'])
        ath = format_tostring_value(info['market_data']['ath']['usd'])
        atl = format_tostring_value(info['market_data']['atl']['usd'])
        rank = info['market_data']['market_cap_rank']
        total_supply = format_tostring_value(info['market_data']['total_supply'])
        max_supply = format_tostring_value(info['market_data']['max_supply'])
        circulating_supply = format_tostring_value(info['market_data']['circulating_supply'])
        current_value = format_tostring_value(info['market_data']['current_price']['usd'])
        return {
            'name': name,
            'logo': logo,
            'site': site,
            'twitter': twitter,
            'reddit': reddit,
            'chat': chat,
            'explorer': explorer,
            'code': source_code,
            'rank': rank,
            'market_cap': market_cap,
            'ath': ath,
            'atl': atl,
            'total_supply': total_supply,
            'max_supply': max_supply,
            'circulating_supply': circulating_supply,
            'current_price': current_value,
            'coin_id': coin_id
        }
    except KeyError as e :
        raise Generic_Error(f"Error: {e}") from e

async def get_crypto_logo(symbol: str) -> Optional[str]:
    """Return logo of token

    Args:
        symbol (str): symbol of coin/token

    Returns:
        Optional[str]: url if exist  url else None
    """
    
    symbol = symbol.upper()
    coin_id = get_value_json('Symbol_id.json', symbol)
    if (coin_id is not None):
        params = {"localization": "false"}
        response = await fetch(f'https://api.coingecko.com/api/v3/coins/{coin_id}', params)
        info = response.json()
        return info['image']['large']
    return None

async def get_exchange_logo(exchange: str) -> Optional[str]:
    """Return logo of exchange

    Args:
        exchange (str): exchange 

    Returns:
        Optional[str]: url if exist  url else None
    """
    response = await fetch(
        f'https://api.coingecko.com/api/v3/exchanges/{exchange}', 
        pass_statuscode=True,
    )
    if response.status != 200:
        return None 

    info = response.json()
    return info['image'] 

def list_exchanges() -> str:
    return ''.join(
        '\n' if (cont % 7 == 0) else f' ** - {exchange} ** '
        for cont, exchange in enumerate(ccxt.exchanges)
    )

async def exchange_info(name: str) -> Dict[str, Any]:
    name = name.lower()
    exchange_id = get_value_json('Exchanges_id.json',name)
    if(exchange_id is None):
        raise Generic_Error('Not found exchange {}'.format(name))
    url = f'https://api.coingecko.com/api/v3/exchanges/{exchange_id}'
    response = await fetch(url)
    info = response.json()
    try:
        name = info['name']
        logo = info['image']
        site = info['url']
        facebook = info['facebook_url']
        telegram = info['telegram_url']
        reddit = info['reddit_url']
        release = info['year_established']
        twitter = ''
        if(info['twitter_handle']):
            twitter = f"https://twitter.com/{info['twitter_handle']}"
        centralized = info['centralized']
        trade_volume_24h_btc = format_tostring_value(info['trade_volume_24h_btc'])
        trade_volume_24h_usd = format_tostring_value(
            Decimal(info['trade_volume_24h_btc']) * await current_price('BTC','USDT')
        )
        return {
            'name': name,
            'logo': logo,
            'site': site,
            'twitter': twitter,
            'reddit': reddit,
            'telegram': telegram,
            'facebook': facebook,
            'release': release,
            'centralized': centralized,
            'trade_volume_24h_btc': trade_volume_24h_btc,
            'trade_volume_24h_usd': trade_volume_24h_usd
        }
    except KeyError as e:
        raise Generic_Error(str(e))

async def get_crypto_exchanges(symbol: str) -> Dict[str, Any]:
    """Returns an exchange list where the token is listed

    Args:
        symbol (str): symbol of coin/token

    Raises:
        Generic_Error: raise in error on status code
        Generic_Not_Found: raise in not found symbol

    Returns:
        Dict[str, Any]
    """
    symbol = symbol.upper()
    coin_id = get_value_json('Symbol_id.json',symbol)
    if(coin_id is None):
        raise Generic_Not_Found(f'Not found symbol {symbol}')
    else:
        url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/tickers'
        response = await fetch(url)
        
        class ticker:
            def __init__(
                self, 
                pair: str, 
                exchange: str, 
                value: str, 
                volume_usd: str, 
                url: str
            ) -> None:
                self.pair = pair
                self.exchange = exchange
                self.value = value
                self.volume_usd = volume_usd
                self.url = url
                
        logo = await get_crypto_logo(symbol)
        info = response.json()
        name = info['name']
        tickers = info['tickers']
        list_crypto_exchanges = list()
        for tckr in tickers:
            if (tckr['base'] == symbol.upper() or tckr['base'] == 'XBT') and (tckr['target'] == 'USDT' or tckr['target'] == 'USD'):
                list_crypto_exchanges.append(
                    ticker(
                        tckr['target'],
                        tckr['market']['name'], 
                        format_tostring_value(tckr['last']), 
                        format_tostring_value(tckr['converted_volume']['usd']),
                        tckr['trade_url']
                    )
                )
        return {
            'name': name,
            'logo': logo,
            'id_symbol': coin_id,
            'list_crypto_exchanges':  list_crypto_exchanges
        }
    raise Generic_Error(f'Error - status code: {response.status}\n url: {url}')

async def get_symbols() -> bool:
    param = {
        'include_platform': 'false'
    }
    response = await fetch('https://api.coingecko.com/api/v3/coins/list', param)
    coins = response.json()
    dic = {}
    path_file = os.path.join(PATH_DATA,'Symbol_id.json')
    for coin in coins:
        symbol = coin['symbol'].upper()
        coin_id = coin['id']
        dic[symbol] = coin_id

    with open(path_file, 'w') as file:
        json.dump(dic, file, indent=2)
    return True

async def get_exchanges() -> bool:
    response = await fetch('https://api.coingecko.com/api/v3/exchanges/list')
    exchanges = response.json()
    dic = {}
    path_file = os.path.join(PATH_DATA,'Exchanges_id.json')
    for exchange in exchanges:
        name = exchange['name'].lower()
        exchange_id = exchange['id']
        dic[name] = exchange_id
        
    with open(path_file, 'w') as file:
        json.dump(dic, file, indent=2)
    return True
