#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging
import re

import discord
from discord import Colour, PartialEmoji
from discord.ext import commands
from configuration import ConfigNode

regional_indicator_emojis = {
    'regional_indicator_a': PartialEmoji(animated=False, name='🇦', id=None),
    'regional_indicator_b': PartialEmoji(animated=False, name='🇧', id=None),
    'regional_indicator_c': PartialEmoji(animated=False, name='🇨', id=None),
    'regional_indicator_d': PartialEmoji(animated=False, name='🇩', id=None),
    'regional_indicator_e': PartialEmoji(animated=False, name='🇪', id=None),
    'regional_indicator_f': PartialEmoji(animated=False, name='🇫', id=None),
    'regional_indicator_g': PartialEmoji(animated=False, name='🇬', id=None),
    'regional_indicator_h': PartialEmoji(animated=False, name='🇭', id=None),
    'regional_indicator_i': PartialEmoji(animated=False, name='🇮', id=None),
    'regional_indicator_j': PartialEmoji(animated=False, name='🇯', id=None),
    'regional_indicator_k': PartialEmoji(animated=False, name='🇰', id=None),
    'regional_indicator_l': PartialEmoji(animated=False, name='🇱', id=None),
    'regional_indicator_m': PartialEmoji(animated=False, name='🇲', id=None),
    'regional_indicator_n': PartialEmoji(animated=False, name='🇳', id=None),
    'regional_indicator_o': PartialEmoji(animated=False, name='🇴', id=None),
    'regional_indicator_p': PartialEmoji(animated=False, name='🇵', id=None),
    'regional_indicator_q': PartialEmoji(animated=False, name='🇶', id=None),
    'regional_indicator_r': PartialEmoji(animated=False, name='🇷', id=None),
    'regional_indicator_s': PartialEmoji(animated=False, name='🇸', id=None),
    'regional_indicator_t': PartialEmoji(animated=False, name='🇹', id=None),
    'regional_indicator_u': PartialEmoji(animated=False, name='🇺', id=None),
    'regional_indicator_v': PartialEmoji(animated=False, name='🇻', id=None),
    'regional_indicator_w': PartialEmoji(animated=False, name='🇼', id=None),
    'regional_indicator_x': PartialEmoji(animated=False, name='🇽', id=None),
    'regional_indicator_y': PartialEmoji(animated=False, name='🇾', id=None),
    'regional_indicator_z': PartialEmoji(animated=False, name='🇿', id=None),
}

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
        poll_msg = await self.get_poll_message_from_command_message(before)
        # check if the message is a poll
        if poll_msg is None:
            return 0

        matches = re.findall('\"(.*?)\"', after.content)
        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=self.build_poll_embed(matches))
        await self.react(poll_msg, matches)

    async def get_poll_message_from_command_message(self, message):
        msg_id = message.id
        channel = message.channel
        for value in self.polls.values():
            meta = value.get('meta')
            if meta.get('command_id') == msg_id:
                return await channel.fetch_message(self.get_key(value))
        return None

    async def send_message(self, ctx, args):
        msg = await ctx.send(embed=self.build_poll_embed(args))
        meta = {
            'command_id': ctx.message.id,
            'is_mv': False,
            'options': args[1:len(args)]
        }
        self.set_poll(msg.id, {'meta': meta, 'votes': dict()}, log=True)
        await self.react(msg, args)

    def build_poll_embed(self, args):
        title = args[0]
        embed = discord.Embed(title=title, color=self.color)
        embed.add_field(name="Options", value=self.build_option(args[1:len(args)]), inline=False)
        embed.set_footer(text='Right click > copy id, to get the id of this poll')
        return embed

    def build_help_embed(self):
        embed = discord.Embed(title="How to use this bot", color=self.color)
        sample = """
               {}poll **make** "Poll title" "option 1" "option 2" ...
               """.format(self.config.get(ConfigNode.PREFIX))
        toggle_mv = """
               {}poll **toggle-mv** <poll-id>
               """.format(self.config.get(ConfigNode.PREFIX))
        edit_sample = """
               To edit a poll, just right click the original command message and edit it there.
               """
        embed.add_field(name="To make a poll", value=sample, inline=False)
        embed.add_field(name="To toggle multiple votes", value=toggle_mv, inline=False)
        embed.add_field(name="To edit a poll", value=edit_sample, inline=False)

        embed.set_footer(text="Be sure to put quotation marks per option.")
        return embed

    def set_poll(self, key, value_dict, log=False):
        self.polls[key] = value_dict
        if log:
            logger.info(self.polls)

    def get_key(self, val):
        for key, value in self.polls.items():
            if val == value:
                return key

    @staticmethod
    def build_option(args):
        options = []
        i = 1
        for option in args:
            options.append(':regional_indicator_{}: \t{}\n'.format(chr(ord('`') + i), option))
            i += 1
        return ''.join(options)

    @staticmethod
    async def react(message, args):
        for i in range(len(args) - 1):
            await message.add_reaction(
                emoji=regional_indicator_emojis.get('regional_indicator_{}'.format(chr(ord('`') + i + 1))))
            await asyncio.sleep(0.25)

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

        # Remove emoji that's not part of the vote
        if payload.emoji not in regional_indicator_emojis.values():
            msg = await channel.fetch_message(payload.message_id)
            await msg.remove_reaction(payload.emoji, payload.member)
            return 0

        poll_dict = self.polls.get(poll_key)
        is_mv = poll_dict.get('meta').get('is_mv')
        user_id = payload.user_id
        # If user voted, delete previous vote.
        if user_id in poll_dict.get('votes').keys() and not is_mv:
            msg = await channel.fetch_message(payload.message_id)
            await msg.remove_reaction(poll_dict.get('votes').get(user_id), payload.member)
            poll_dict.get('votes')[user_id] = payload.emoji
            self.set_poll(poll_key, poll_dict, log=True)
        # Else just log it
        else:
            poll_dict.get('votes')[user_id] = payload.emoji
            self.set_poll(poll_key, poll_dict, log=True)

    @commands.command()
    async def help(self, ctx):
        await ctx.send(embed=self.build_help_embed())

    @commands.group()
    async def poll(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=self.build_help_embed())

    @poll.command()
    async def make(self, ctx, *args):
        if ctx.invoked_subcommand is None:
            """Poll commands"""
            if len(args) is 0:
                await ctx.send(embed=self.build_help_embed())
                return 0
            if len(args) is 1:
                await ctx.send(embed=self.build_help_embed())
                return 0
            await self.send_message(ctx, args)

    @poll.command(name='toggle-mv')
    async def toggle_mv(self, ctx, message_id: int):
        if message_id not in self.polls.keys():
            return 0
        is_mv = self.polls.get(message_id).get('meta').get('is_mv')
        is_mv = not is_mv
        self.polls.get(message_id).get('meta')['is_mv'] = is_mv
        logger.info(self.polls)
        desc = "Users can now vote multiple times for `{}`.".format(message_id) if is_mv \
            else "Users can no longer vote multiple times for `{}`.".format(message_id)
        embed = discord.Embed(description=desc, color=self.color)
        await ctx.send(embed=embed)
