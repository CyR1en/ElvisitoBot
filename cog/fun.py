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
        self.cache = dict()
        self.banned_servers = bot.config_file.get_list_node(ConfigNode.BLACKLIST)
        u_name = bot.config_file.get(ConfigNode.R_UNAME)
        u_pass = bot.config_file.get(ConfigNode.R_PASS)
        self.r = praw.Reddit(client_id=bot.config_file.get(ConfigNode.R_C_ID),
                             client_secret=bot.config_file.get(ConfigNode.R_C_SECRET),
                             user_agent=USER_AGENT.format(os.name, u_name),
                             username=u_name,
                             password=u_pass)

    @commands.command()
    async def reddit(self, ctx, sub):
        if sub in self.banned_servers:
            e = discord.Embed(description="Broo, are you serious? That's got some f'ed up content...".format(sub))
            await ctx.send(embed=e)
            return 0
        try:
            posts = await self._get_posts(sub)
            await ctx.send(embed=await self._get_content(posts, sub))
        except prawcore.exceptions.NotFound:
            e = discord.Embed(description="Yo bro, `r/{}` doesn't exist bro...".format(sub))
            await ctx.send(embed=e)
        except NotFound:
            e = discord.Embed(description="Dang bro, `r/{}` doesn't exist bro...".format(sub))
            await ctx.send(embed=e)
        except prawcore.exceptions.Redirect:
            e = discord.Embed(description="Yo, `r/{}` doesn't exist bro...".format(sub))
            await ctx.send(embed=e)

    @commands.command()
    async def clearcache(self, ctx):
        self.cache = dict()
        print(self.cache)
        await ctx.send(embed=discord.Embed(description='Cleared cache!'))

    async def _get_posts(self, sub):
        posts = None
        if sub not in self.cache:
            sub = self.r.subreddit(sub)
            posts = [post for post in sub.hot(limit=200)]
            self.cache[sub] = posts
        else:
            posts = self.cache.get(sub)
        return posts

    async def _get_content(self, posts, sub):
        try:
            random_post = random.choice(posts)
            if not self._validate(random_post.url):
                self.cache.get(sub).remove(random_post)
                return await self._get_content(posts, sub)
            else:
                embed = discord.Embed(title="Here you go bro, it's from r/{}".format(sub), description='{}'.format(random_post.title))
                embed.set_image(url=random_post.url)
                return embed
        except RecursionError:
            return discord.Embed(description="Broo, there's no great content in this sub!")
        except IndexError:
            return discord.Embed(description="Wtf bro, this sub doesn't have a lot of posts...")

    @staticmethod
    def _validate(link):
        if not link.startswith('https:'):
            return False
        ext = ['.jpg', '.png', '.gif', ]
        for e in ext:
            if link.endswith(e):
                return True
        return False
