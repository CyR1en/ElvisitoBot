import logging
import sys

import discord
from discord import Colour
from discord.ext import commands

from cog.poll import Poll

logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self, config_file, command_prefix="$", color=Colour.from_rgb(15, 185, 177), **options):
        super().__init__(command_prefix, **options)
        self.color = color
        self.config_file = config_file
        self.token = None
        self.remove_command('help')
        self.add_cog(Poll(self, self.config_file, self.color))

    async def on_ready(self):
        game = "$poll"
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=game))
        logger.info('Successfully logged in as {}'.format(self.user))
