#  MIT License
#
#  Copyright (c) 2020 Ethan Bacurio
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
import random

import discord
from discord.ext import commands


class Elvisito(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def elvisito(self, ctx):
        channel = ctx.guild.get_channel(703500380713123900)
        messages = list(await channel.history(limit=1000).flatten())
        moment = await self.get_moment(messages)
        await ctx.send(embed=self._embed(moment, channel))
        return 0

    def _embed(self, message, channel):
        embed = discord.Embed(color=self.bot.color)
        if self._is_url(message) and not self._is_vid_link(message):
            embed.set_image(url=message)
        else:
            message = self._clean_message(message)
            embed.add_field(name='Elvisito Moment', value='\"{}\"'.format(message))
        embed.set_footer(text="Moments from #{}".format(channel.name))
        return embed

    def _is_vid_link(self, link):
        ext = ['.mp4', '.mov', '.mkv']
        for e in ext:
            if link.endswith(e):
                return True
        return False

    def _clean_message(self, message):
        if '-elvis' in message:
            message = message.replace('-elvis', '')
        elif '-Elvis' in message:
            message = message.replace('-Elvis', '')
        return message.strip("\"").strip('”')

    def _is_url(self, string_url):
        import re
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, string_url) is not None

    async def get_moment(self, messages):
        msg = random.choice(messages)
        if msg.content.lower() == '-elvis':
            return await self.get_moment(messages)
        if msg.attachments:
            return msg.attachments[0].url
        else:
            return msg.content
