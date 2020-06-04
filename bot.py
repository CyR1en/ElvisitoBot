import logging
import random

import discord
from discord import Colour
from discord.ext import commands
from discord.ext.commands import CommandNotFound

from cog.admin import Admin
from cog.elvisito import Elvisito
from cog.fun import Reddit
from cog.misc import Misc
from cog.poll import Poll
from cog.voice import Music
from configuration import ConfigNode
from exceptions import PathDoesNotExist

logger = logging.getLogger(__name__)

phrases = ["Bro, wtf is `{}`",
           "Are you serious bro? I don't fuckin know bro...",
           "Shiz, what is `{}` bro",
           "Oh bro, idk what that is",
           "Oh shoes, my bad my bad. I don't know what `{}` is bro...",
           "Wtf is {}. You should buy an IronFlask though",
           "Brooooo... `{}`? bro..."]


class Bot(commands.AutoShardedBot):
    def __init__(self, config_file, color=Colour.from_rgb(15, 185, 177), **options):
        super().__init__(config_file.get_tuple_node(ConfigNode.PREFIX), **options)
        self.color = color
        self.config_file = config_file
        self.token = None
        self.remove_command('help')
        self.add_cog(Poll(self))
        self.add_cog(Admin(self))
        self.add_cog(Elvisito(self))
        self.add_cog(Misc(self))
        self.add_cog(Reddit(self))
        self.add_cog(Music(self))

    async def on_ready(self):
        game = "{}help".format(self.config_file.get_tuple_node(ConfigNode.PREFIX)[0])
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=game))
        logger.info('Successfully logged in as {}'.format(self.user))

    def start_bot(self):
        self.run(self.config_file.get(ConfigNode.TOKEN))

    async def on_command_error(self, context, exception):
        if isinstance(exception, CommandNotFound):
            content = str(context.message.content)
            if content.startswith('elvis '):
                return
            phrase = str(random.choice(phrases))
            i_cmd = self.remove_prefix(content)
            reply = phrase.format(i_cmd) if '{}' in phrase else phrase
            await context.channel.send(reply)
            return
        if isinstance(exception, PathDoesNotExist):
            query = str(exception.original)
            phrase = str(random.choice(phrases))
            reply = phrase.format(query) if '{}' in phrase else phrase
            await context.channel.send(reply)
            return
        raise exception

    def remove_prefix(self, content: str):
        prefixes = self.config_file.get_tuple_node(ConfigNode.PREFIX)
        print(prefixes)
        for p in prefixes:
            if p in content:
                return content.replace(p, "")
        return content
