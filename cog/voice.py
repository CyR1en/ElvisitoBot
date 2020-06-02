import asyncio
import os
from os import listdir
from os.path import isfile, join

import discord
import youtube_dl
from discord import Embed
from discord.ext import commands
# Suppress noise about console usage from errors
from discord.ext.commands import CommandInvokeError
from youtube_search import YoutubeSearch

from exceptions import PathDoesNotExist, NotInChannel
from utility import URL

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'dl/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        print(filename)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def from_query(cls, query, *, loop=None, stream=False):
        link = await cls.search_url(query)
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def search_url(cls, query):
        results = YoutubeSearch(query, max_results=1).to_dict()
        return "https://www.youtube.com{}".format(results[0].get('link'))


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def say(self, ctx, *, query):
        path = os.path.join(os.getcwd(), 'audio', "{}.mp3".format(query))
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(path))
        ctx.voice_client.play(source, after=lambda e: self._disconnect(ctx, e))
        await ctx.send('Alright bro')

    @commands.command()
    async def saylist(self, ctx):
        path = os.path.join(os.getcwd(), 'audio')
        files = [f for f in listdir(path) if isfile(join(path, f))]
        s = ", "
        s = s.join(files).replace(".mp3", "")
        msg = "Alright bro, here's what you could ask me to say. `{}`".format(s)
        await ctx.send(msg)

    def _disconnect(self, ctx, error):
        coro = ctx.voice_client.disconnect()
        fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
        try:
            fut.result()
        except:
            pass

    @commands.command()
    async def play(self, ctx, *, arg):
        async with ctx.typing():
            player = None
            if URL.is_url(arg):
                player = await YTDLSource.from_url(arg, loop=self.bot.loop)
            else:
                player = await YTDLSource.from_query(arg, loop=self.bot.loop)
            print(player.__dict__)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        embed = Embed()
        embed.add_field(name="Alright, here you go bro", value='[{}]({})'.format(player.title, player.url),
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def shutup(self, ctx):
        await ctx.send("Shiz, alright bro, I'm sorry")
        await ctx.voice_client.disconnect()

    @say.before_invoke
    async def ensure_data(self, ctx):
        content = ctx.message.content
        query = content[content.index('say') + len('say'):len(content)].strip()
        path = os.path.join(os.getcwd(), 'audio', "{}.mp3".format(query))
        if not os.path.exists(path):
            raise PathDoesNotExist(str(path))
        else:
            await self.ensure_voice(ctx)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Bro, you're not even on a voice channel")
                raise NotInChannel("You're not in a voice channel")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
