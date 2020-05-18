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
import prawcore
from discord import NotFound
from discord.ext import commands
import praw
import os

from discord.ext.commands import CommandInvokeError

from configuration import ConfigNode

USER_AGENT = '{}:com.cyr1en.somebot:v0.1.0 (by /u/{})'


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        u_name = bot.config_file.get(ConfigNode.R_UNAME)
        u_pass = bot.config_file.get(ConfigNode.R_PASS)
        self.r = praw.Reddit(client_id=bot.config_file.get(ConfigNode.R_C_ID),
                             client_secret=bot.config_file.get(ConfigNode.R_C_SECRET),
                             user_agent=USER_AGENT.format(os.name, u_name),
                             username=u_name,
                             password=u_pass)

    @commands.command()
    async def reddit(self, ctx, sub):
        if sub in self.bot.config_file.get_list_node(ConfigNode.BLACKLIST):
            await ctx.send('That subreddit is banned from this server')
            return 0
        try:
            sub = self.r.subreddit(sub)
            posts = [post for post in sub.hot(limit=200)]
            del posts[0]
            await ctx.send(embed=await self.get_content(posts, sub))
        except prawcore.exceptions.NotFound:
            e = discord.Embed(description="Yo, `r/{}` doesn't exist bro...".format(sub))
            await ctx.send(embed=e)
        except NotFound:
            e = discord.Embed(description="Yo, `r/{}` doesn't exist bro...".format(sub))
            await ctx.send(embed=e)
        except prawcore.exceptions.Redirect:
            e = discord.Embed(description="Yo, `r/{}` doesn't exist bro...".format(sub))
            await ctx.send(embed=e)

    async def get_content(self, posts, sub):
        try:
            random_post = random.choice(posts)
            if not self._validate(random_post.url):
                return await self.get_content(posts, sub)
            else:
                embed = discord.Embed(title='r/{}'.format(sub), description='{}'.format(random_post.title))
                embed.set_image(url=random_post.url)
                return embed
        except RecursionError:
            return discord.Embed(description="Dang, there's no great content in this sub!")
        except IndexError:
            return discord.Embed(description="Wtf, this sub doesn't have a lot of posts...")

    @staticmethod
    def _validate(link):
        if not link.startswith('https:'):
            return False
        ext = ['.jpg', '.png', '.gif', ]
        for e in ext:
            if link.endswith(e):
                return True
        return False
