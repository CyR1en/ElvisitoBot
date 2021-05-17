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
from discord.ext import commands, tasks
import praw
import os
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
        self._refresh_cache.start()

    @commands.command()
    async def reddit(self, ctx, sub):
        u_name = ctx.author.name
        if sub in self.banned_servers:
            e = discord.Embed(
                description="Yo {}, are you serious bro? That's got some f'ed up content...".format(u_name))
            await ctx.send(embed=e)
            return 0
        try:
            posts = await self._get_posts(sub)
            await ctx.send(embed=await self._get_content(u_name, posts, sub))
        except prawcore.exceptions.Forbidden:
            e = discord.Embed(description="Oh shiz, it says it's forbidden bro, I don't fuckin know.".format(sub))
            await ctx.send(embed=e)
        except prawcore.exceptions.NotFound:
            e = discord.Embed(description="Yo bro, I can't find `r/{}`...".format(sub))
            await ctx.send(embed=e)
        except NotFound:
            e = discord.Embed(description="Dang bro, `r/{}` doesn't exist bro...".format(sub))
            await ctx.send(embed=e)
        except prawcore.exceptions.Redirect:
            e = discord.Embed(description="Shoes, I got lost looking for `r/{}`...".format(sub))
            await ctx.send(embed=e)

    @commands.command()
    async def clearcache(self, ctx):
        self.cache = dict()
        await ctx.send(embed=discord.Embed(description="Alright bro, It's all clean now bro"))

    async def _get_posts(self, sub):
        if not self._is_sub_cached(sub):
            posts = await self._cache_sub(sub)
        else:
            posts = self.cache.get(sub)
        return posts

    async def _cache_sub(self, sub):
        """
        Cache subreddit and return the posts on that subreddit.
        """
        sub = self.r.subreddit(sub)
        posts = [post for post in sub.hot(limit=500)]
        for p in posts:
            if not self._validate(p.url):
                posts.remove(p)
        self.cache[str(sub)] = posts
        return posts

    def _is_sub_cached(self, sub):
        sub1 = str(sub)
        for s in self.cache.keys():
            if s.lower() == sub1.lower():
                return True
        return False

    @tasks.loop(hours=24)
    async def _refresh_cache(self):
        subs = self.cache.keys()
        self.cache = dict()
        for sub in subs:
            await self._cache_sub(sub)

    async def _get_content(self, u_name, posts, sub):
        try:
            random_post = random.choice(posts)
            if not self._validate(random_post.url):
                self.cache.get(sub).remove(random_post)
                return await self._get_content(u_name, posts, sub)
            else:
                embed = discord.Embed(title="Here you go bro, it's from r/{}".format(sub),
                                      description='{}'.format(random_post.title))
                embed.set_image(url=random_post.url)
                embed.set_footer(text="{}, Enjoy this bro".format(u_name))
                return embed
        except RecursionError:
            return discord.Embed(description="Broo, there's no great content in this sub!")
        except IndexError:
            return discord.Embed(description="Wtf bro, this sub doesn't have a lot of posts...")

    @staticmethod
    def _validate(link):
        if not link.startswith('https:'):
            return False
        link.replace('.gifv', '.gif')
        ext = ['.jpg', '.png', '.gif', '.jpeg']
        for e in ext:
            if link.endswith(e):
                return True
        return False
