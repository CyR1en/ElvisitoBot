import logging
import sys
from discord import Colour
from discord.ext import commands

from cog.poll import Poll
from configuration import ConfigFile, ConfigNode

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, color=Colour.from_rgb(15, 185, 177)):
        self.color = color
        self.config_file = ConfigFile("config")
        self.token = None
        self.bot = commands.Bot(command_prefix=self.get_prefix())
        self.bot.remove_command('help')
        self.bot.add_cog(Poll(self.bot, self.config_file, self.color))
        self.run()

    def get_prefix(self):
        prefix = self.config_file.get_string_node(ConfigNode.PREFIX)
        return '$' if not prefix else prefix

    def run(self):
        self.token = self.config_file.get_string_node(ConfigNode.TOKEN)
        if self.token == ConfigNode.TOKEN.get_value():
            logger.warning("The config file is either newly generated or the token was left to its default value. \n"
                           "Please enter your bot's token:")
            try:
                self.token = input()
                self.config_file.set(ConfigNode.TOKEN, self.token)
            except KeyboardInterrupt:
                logger.error("Interrupted token input")
                sys.exit()
        self.bot.run(self.token)
