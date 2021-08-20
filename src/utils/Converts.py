from discord.ext import commands
from typing import Union, Optional

from .Checks import Generic_Not_Found

class Timeframe:
    TIMEFRAMES = {
        '1m': '1 minute',
        '3m': '3 minutes',
        '5m': '5 minutes',
        '15m': '15 minutes',
        '30m': '30 minutes',
        '1h': '1 hour',
        '2h': '2 hours',
        '4h': '4 hours',
        '6h': '6 hours',
        '8h': '8 hours',
        '12h': '12 hours',
        '1d': '1 day',
        '3d': '3 days',
        '1w': '1 week',
        '1M': '1 Month',
    }
    timeframe_limit = ('1m', '3m', '5m', '15m')
    def __init__(self, timeframe: str):
        self.timeframe = timeframe
        self.limit = 300 if timeframe in Timeframe.timeframe_limit else 150
    
    def __str__(self) -> str:
        return Timeframe.TIMEFRAMES[self.timeframe]
    
    def __eq__(self) -> str:
        return self.timeframe

class Convert_to_Timeframes(commands.Converter):
    async def convert(self, ctx, argument: str) -> Union[str, Timeframe]:
        if argument in Timeframe.TIMEFRAMES:
            return Timeframe(argument)
        return int(argument) if argument.isnumeric() else argument

class Convert_Timeframes(Convert_to_Timeframes):
    async def convert(self, ctx, argument: str) -> Timeframe:
        if argument in Timeframe.TIMEFRAMES:
            return Timeframe(argument)
        try:
            return int(argument)
        except ValueError:
            raise Generic_Not_Found(f"Not found interval {argument}")
