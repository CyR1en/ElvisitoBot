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
import discord
from discord.ext import commands

from configuration import ConfigNode


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = bot.color
        self.config = bot.config_file

    @commands.command()
    async def help(self, ctx):
        await ctx.send(embed=Misc.build_help_embed(self))

    @staticmethod
    def build_help_embed(self):
        prefix = format(self.config.get_tuple_node(ConfigNode.PREFIX)[0])
        embed = discord.Embed(title="Alright bro, this is how you use this bot bro", color=self.color)
        sample = """
                  {}poll **make** "Poll title" "option 1" "option 2" ...
                  """.format(prefix)
        toggle_mv = """
                  {}poll **toggle-mv** <poll-id>
                  """.format(prefix)
        edit_sample = """
                  To edit a poll, just right click the original command message and edit it bro.
                  """
        reddit = """
                {}reddit <subreddit>
                """.format(prefix)
        embed.add_field(name="To make a poll", value=sample, inline=False)
        embed.add_field(name="To toggle multiple votes", value=toggle_mv, inline=False)
        embed.add_field(name="To edit a poll", value=edit_sample, inline=False)
        embed.add_field(name="To get some Reddit content", value=reddit, inline=False)
        embed.add_field(name="For an Elvisito moment", value="{}elvisito".format(prefix))

        embed.set_footer(text="Oh for polls, be sure to put quotation marks per option.")
        return embed
