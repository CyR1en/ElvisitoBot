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
            random_post = random.choice(posts)
            await ctx.send(random_post.url)
        except CommandInvokeError:
            await ctx.send('`{} is not a subreddit`'.format(sub))
        except prawcore.exceptions.NotFound:
            await ctx.send('`404: Cannot find /r/{}`'.format(sub))
        except NotFound:
            await ctx.send('`404: Cannot find /r/{}`'.format(sub))
