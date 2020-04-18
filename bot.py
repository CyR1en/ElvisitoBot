import logging
import sys
import time
import re
import discord.ext
from discord import PartialEmoji, Colour
from discord.ext import commands

from configuration import ConfigFile, ConfigNode

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
fmt = logging.Formatter('[%(levelname)s][%(asctime)s][%(name)s]: %(message)s')
handler.setFormatter(fmt)
s_handler = logging.StreamHandler()
s_handler.setFormatter(fmt)
logger.addHandler(handler)
logger.addHandler(s_handler)

config_file = ConfigFile("config")
embed_color = Colour.from_rgb(15, 185, 177)

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


def get_prefix():
    prefix = config_file.get_string_node(ConfigNode.PREFIX)
    return '$' if not prefix else prefix


bot = commands.Bot(command_prefix=get_prefix())
bot.remove_command('help')

token = config_file.get_string_node(ConfigNode.TOKEN)
if token == ConfigNode.TOKEN.get_value():
    logger.warning("The config file is either newly generated or the token was left to its default value. \n"
                   "Please enter your bot's token:")
    try:
        token = input()
        config_file.set(ConfigNode.TOKEN, token)
    except KeyboardInterrupt:
        logger.error("Interrupted token input")
        sys.exit()


@bot.event
async def on_ready():
    game = "{}poll".format(config_file.get_string_node(ConfigNode.PREFIX))
    activity = discord.Game(name=game, type=2)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=game))
    logger.info('Successfully logged in as {}'.format(bot.user))


polls = dict()


@bot.event
async def on_raw_message_delete(payload):
    key = payload.message_id
    if key in polls.keys():
        del polls[key]
        logger.info(polls)


@bot.event
async def on_message_edit(before, after):
    poll_msg = await get_poll_message_from_command_message(before)
    # check if the message is a poll
    print(poll_msg)
    print(after)
    if poll_msg is None:
        return 0

    matches = re.findall('\"(.*?)\"', after.content)
    print(before.content)
    print(after.content)
    print(matches)
    await poll_msg.clear_reactions()
    await poll_msg.edit(embed=build_poll_embed(matches))
    await react(poll_msg, matches)


async def get_poll_message_from_command_message(message):
    msg_id = message.id
    channel = message.channel
    print(polls.values())
    for value in polls.values():
        print(msg_id)
        print(value.get('command_id'))
        if value.get('command_id') == msg_id:
            return await channel.fetch_message(get_key(value))
    return None


def get_key(val):
    for key, value in polls.items():
        if val == value:
            return key


@bot.event
async def on_raw_reaction_add(payload):
    # Ignore if self is adding reaction
    if payload.user_id == bot.user.id:
        return 0

    channel = bot.get_channel(payload.channel_id)
    poll_key = payload.message_id
    # Check if this message is a tracked poll
    if poll_key not in polls.keys():
        return 0

    # Remove emoji that's not part of the vote
    if payload.emoji not in regional_indicator_emojis.values():
        msg = await channel.fetch_message(payload.message_id)
        await msg.remove_reaction(payload.emoji, payload.member)
        return 0

    poll_dict = polls.get(poll_key)
    user_id = payload.user_id
    # If user voted, delete previous vote.
    if user_id in poll_dict.keys():
        msg = await channel.fetch_message(payload.message_id)
        await msg.remove_reaction(poll_dict.get(user_id), payload.member)
        poll_dict[user_id] = payload.emoji
        set_poll(poll_key, poll_dict, log=True)
    # Else just log it
    else:
        poll_dict[user_id] = payload.emoji
        set_poll(poll_key, poll_dict, log=True)


@bot.command()
async def help(ctx):
    await ctx.send(embed=build_help_embed())


@bot.command()
async def poll(ctx, *args):
    """Poll commands"""
    if len(args) is 0:
        await ctx.send(embed=build_help_embed())
        return 0
    if len(args) is 1:
        await ctx.send(embed=build_help_embed())
        return 0

    await send_message(ctx, args)


@bot.command()
async def purge(ctx, number: int):
    channel = ctx.channel
    await ctx.message.delete()
    await channel.purge(limit=number)


async def send_message(ctx, args):
    msg = await ctx.send(embed=build_poll_embed(args))
    set_poll(msg.id, {'command_id': ctx.message.id}, log=True)
    await react(msg, args)


async def react(message, args):
    for i in range(len(args) - 1):
        await message.add_reaction(
            emoji=regional_indicator_emojis.get('regional_indicator_{}'.format(chr(ord('`') + i + 1))))
        time.sleep(0.25)


def build_poll_embed(args):
    title = args[0]
    embed = discord.Embed(title=title, color=embed_color)
    embed.add_field(name="Options", value=build_option(args[1:len(args)]), inline=False)
    return embed


def build_option(args):
    options = []
    i = 1
    for option in args:
        options.append(':regional_indicator_{}: \t{}\n'.format(chr(ord('`') + i), option))
        i += 1
    return ''.join(options)


def build_help_embed():
    embed = discord.Embed(title="How to use this bot", color=embed_color)
    sample = """
           {}poll "Poll title" "option 1" "option 2" ...
           """.format(config_file.get_string_node(ConfigNode.PREFIX))
    edit_sample = """
           To edit a poll, just right click the original command message and edit it there.
           """
    embed.add_field(name="To make a poll", value=sample, inline=False)
    embed.add_field(name="To edit a poll", value=edit_sample, inline=False)
    embed.set_footer(text="Be sure to put quotation marks per option.")
    return embed


def set_poll(key, value_dict, log=False):
    polls[key] = value_dict
    if log:
        logger.info(polls)


bot.run(token)
