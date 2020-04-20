import logging

import discord
from discord import Colour
from discord.ext import commands

from cog.poll import Poll
from configuration import ConfigNode

logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self, config_file, color=Colour.from_rgb(15, 185, 177), **options):
        super().__init__(config_file.get(ConfigNode.PREFIX), **options)
        self.color = color
        self.config_file = config_file
        self.token = None
        self.remove_command('help')
        self.add_cog(Poll(self, self.config_file, self.color))

    async def on_ready(self):
        game = "{}poll".format(self.config_file.get(ConfigNode.PREFIX))
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=game))
        logger.info('Successfully logged in as {}'.format(self.user))

    def start(self):
        self.run(self.config_file.get(ConfigNode.TOKEN))
