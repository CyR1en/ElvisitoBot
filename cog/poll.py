# -*- coding: utf-8 -*-

import asyncio
import logging
import re

import discord
from discord import PartialEmoji
from discord.ext import commands

from cog.misc import Misc
from configuration import ConfigNode
from utility import DictAccess

F20 = 0x171971A1080
D_EPOCH = 0x14AA2CAB000

ri_emoji = [
    PartialEmoji(animated=False, name='🇦', id=None),
    PartialEmoji(animated=False, name='🇧', id=None),
    PartialEmoji(animated=False, name='🇨', id=None),
    PartialEmoji(animated=False, name='🇩', id=None),
    PartialEmoji(animated=False, name='🇪', id=None),
    PartialEmoji(animated=False, name='🇫', id=None),
    PartialEmoji(animated=False, name='🇬', id=None),
    PartialEmoji(animated=False, name='🇭', id=None),
    PartialEmoji(animated=False, name='🇮', id=None),
    PartialEmoji(animated=False, name='🇯', id=None),
    PartialEmoji(animated=False, name='🇰', id=None),
    PartialEmoji(animated=False, name='🇱', id=None),
    PartialEmoji(animated=False, name='🇲', id=None),
    PartialEmoji(animated=False, name='🇳', id=None),
    PartialEmoji(animated=False, name='🇴', id=None),
    PartialEmoji(animated=False, name='🇵', id=None),
    PartialEmoji(animated=False, name='🇶', id=None),
    PartialEmoji(animated=False, name='🇷', id=None),
    PartialEmoji(animated=False, name='🇸', id=None),
    PartialEmoji(animated=False, name='🇹', id=None),
    PartialEmoji(animated=False, name='🇺', id=None),
    PartialEmoji(animated=False, name='🇻', id=None),
    PartialEmoji(animated=False, name='🇼', id=None),
    PartialEmoji(animated=False, name='🇽', id=None),
    PartialEmoji(animated=False, name='🇾', id=None),
    PartialEmoji(animated=False, name='🇿', id=None),
]

logger = logging.getLogger(__name__)


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config_file
        self.color = bot.color
        self.polls = dict()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        key = payload.message_id
        if key in self.polls.keys():
            del self.polls[key]
            logger.info(self.polls)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        poll_msg = await self.get_poll_from_id(before)
        # check if the message is a poll
        if poll_msg is None:
            return 0

        model = self.polls.get(poll_msg.id)
        matches = re.findall('\"(.*?)\"', after.content)
        model.set_meta('title', matches[0])
        model.set_meta('options', matches[1:len(matches)])
        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=self._build_poll_embed(poll_id=poll_msg.id))
        await self._react(poll_msg)

    async def get_poll_from_id(self, message):
        msg_id = message.id
        channel = message.channel
        for value in self.polls.values():
            if value.get_meta('command_id') == msg_id:
                return await channel.fetch_message(self._get_key(value))
        return None

    def _build_poll_embed(self, poll_id):
        args = self.polls.get(poll_id).get_meta('options')
        title = self.polls.get(poll_id).get_meta('title')
        embed = discord.Embed(title=title, color=self.color)

        options = []
        i = 1
        for option in self.polls.get(poll_id).get_meta('options'):
            options.append(':regional_indicator_{}: \t{}\n'.format(chr(ord('`') + i), option))
            i += 1
        options = ''.join(options)

        embed.add_field(name="Options", value=self._build_option(poll_id), inline=False)
        embed.set_footer(text='Poll ID: {}'.format(poll_id))
        return embed

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Ignore if self is adding reaction
        if payload.user_id == self.bot.user.id:
            return 0

        channel = self.bot.get_channel(payload.channel_id)
        poll_key = payload.message_id
        # Check if this message is a tracked poll
        if poll_key not in self.polls.keys():
            return 0

        # Remove emoji that's not an option
        if payload.emoji not in ri_emoji[0:len(self.polls.get(poll_key).get_meta('options'))]:
            msg = await channel.fetch_message(payload.message_id)
            await msg.remove_reaction(payload.emoji, payload.member)
            return 0

        model = self.polls.get(poll_key)
        user_id = payload.user_id
        # If user voted, delete previous vote.
        if user_id in model.votes.keys() and not model.get_meta('is_mv'):
            msg = await channel.fetch_message(payload.message_id)
            await msg.remove_reaction(model.get_vote(user_id), payload.member)
            model.set_vote(user_id, payload.emoji)
        # Else just log it
        else:
            model.set_vote(user_id, payload.emoji)

    @commands.group()
    async def poll(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=Misc.build_help_embed(self))

    @poll.command()
    async def make(self, ctx, *args):
        ctx.channel.guild.get_member('')
        if ctx.invoked_subcommand is None:
            """Poll commands"""
            if len(args) is 0:
                await ctx.send(embed=Misc.build_help_embed(self))
                return 0
            if len(args) is 1:
                await ctx.send(embed=Misc.build_help_embed(self))
                return 0
            await self._send_message(ctx, args)

    @poll.command(name='toggle-mv')
    async def toggle_mv(self, ctx, message_id: int):
        if message_id not in self.polls.keys():
            return 0
        model = self.polls.get(message_id)
        is_mv = model.get_meta('is_mv')
        model.set_meta('is_mv', not is_mv)
        logger.info(self.polls)
        desc = "Users can now vote multiple times for `{}`.".format(model.get_meta('title')) if not is_mv \
            else "Users can no longer vote multiple times for `{}`.".format(model.get_meta('title'))
        embed = discord.Embed(description=desc, color=self.color)
        await ctx.send(embed=embed)

    def _new_poll(self, key, poll_model, log=False):
        self.polls[key] = poll_model
        if log:
            logger.info(self.polls)

    async def _send_message(self, ctx, args):
        msg = await ctx.send(embed=discord.Embed(title="Generating poll...."))
        self._new_poll(msg.id, PollModel(ctx.message.id, args), log=True)
        await msg.edit(embed=self._build_poll_embed(msg.id))
        await self._react(msg)

    def _get_key(self, val):
        for key, value in self.polls.items():
            if val == value:
                return key

    def _build_option(self, poll_id):
        options = []
        i = 1
        for option in self.polls.get(poll_id).get_meta('options'):
            options.append(':regional_indicator_{}: \t{}\n'.format(chr(ord('`') + i), option))
            i += 1
        return ''.join(options)

    async def _react(self, message):
        args = self.polls.get(message.id).get_meta('options')
        message = await message.channel.fetch_message(id=message.id)
        for i in range(len(args)):
            await message.add_reaction(
                emoji=ri_emoji[i])
            await asyncio.sleep(0.25)

    @staticmethod
    def shorten_snowflake(snowflake):
        elapsed = (snowflake >> 0x16) + D_EPOCH
        dT = elapsed - F20
        return (dT << 5) | (snowflake & 0xFFF)

    @staticmethod
    def expand_shortflake(snowflake):
        diff = F20 - D_EPOCH
        print(diff)
        full = ((snowflake >> 5) + diff) << 0x16
        print(full)
        return ((snowflake >> 5) + diff) << 0x16


if __name__ == "__main__":
    flake = 703149926741442692
    short_flake = Poll.shorten_snowflake(flake)
    print(short_flake)
    print(flake)
    print(Poll.expand_shortflake(short_flake))


class PollModel(DictAccess):
    def __init__(self, command_id, args, is_mv=False):
        self.meta = {'command_id': command_id, 'title': args[0], 'options': args[1:len(args)], 'is_mv': is_mv}
        self.votes = dict()

    @DictAccess.get
    def get_meta(self, key):
        return self.meta

    @DictAccess.set
    def set_meta(self, key, val):
        return self.meta

    @DictAccess.get
    def get_vote(self, key):
        return self.votes

    @DictAccess.set
    def set_vote(self, key, val):
        return self.votes

    def __repr__(self):
        return '<{0.__class__.__name__} meta={0.meta} votes={0.votes}>'.format(self)
