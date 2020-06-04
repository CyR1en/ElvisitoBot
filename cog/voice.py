import asyncio
import os
from collections import deque
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
        return await cls.get_data(url, loop=cls.get_loop(loop), stream=stream)

    @classmethod
    async def from_query(cls, query, *, loop=None, stream=False):
        link = await cls.search_url(query)
        return await cls.get_data(link, loop=cls.get_loop(loop), stream=stream)

    @classmethod
    def get_loop(cls, loop=None):
        return loop or asyncio.get_event_loop()

    @classmethod
    async def get_data(cls, url, *, loop=None, stream=False):
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def search_url(cls, query):
        results = YoutubeSearch(query, max_results=10).to_dict()
        print(results)
        return "https://www.youtube.com{}".format(results[0].get('link'))


class Queue:
    def __init__(self):
        self.stack = []

    def queue(self, item):
        self.stack.append(item)

    def next(self):
        if len(self.stack) > 0:
            return self.stack.pop(0)
        return None

    def peek(self):
        return self.stack[len(self.stack) - 1]

    def queued(self):
        return len(self.stack)


class Music(commands.Cog):
    def __init__(self, bot):
        self.audio_dir = os.path.join(os.getcwd(), 'audio')
        self.curr_audio_dir = os.path.join(self.audio_dir, 'elvis')
        self._queue = Queue()
        self.now_playing_message = None
        self.bot = bot

    @commands.command()
    async def imitate(self, ctx, directory: str):
        dirs = [f for f in listdir(self.audio_dir)]
        if directory not in dirs:
            await ctx.send("Bro, I don't know how to imitate that person...")
        else:
            self.curr_audio_dir = os.path.join(self.audio_dir, directory)
            msg = "Alright bro, I'm now imitating `{}`.".format(directory)
            await ctx.send(msg)

    @commands.command()
    async def imitatelist(self, ctx):
        dirs = [f for f in listdir(self.audio_dir)]
        s = ", "
        s = s.join(dirs)
        msg = "Alright bro, I could imitate the following people. `{}`".format(s)
        await ctx.send(msg)

    @commands.command()
    async def say(self, ctx, *, query):
        voices = str(query).strip().split(" ")
        for v in voices:
            path = os.path.join(self.curr_audio_dir, "{}.mp3".format(v))
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(path))
            self._queue.queue(source)
        if not ctx.voice_client.is_playing():
            await self._play(ctx)
        await ctx.send('Alright bro')

    @commands.command()
    async def saylist(self, ctx):
        path = self.curr_audio_dir
        files = [f for f in listdir(path) if isfile(join(path, f))]
        s = ", "
        s = s.join(files).replace(".mp3", "")
        msg = "Alright bro, here's what you could ask me to say. `{}`".format(s)
        await ctx.send(msg)

    @commands.command()
    async def play(self, ctx, *, arg):
        async with ctx.typing():
            # Just queue the song
            await self.queue(ctx, arg=arg)

    async def _play(self, ctx):
        # get the next song
        source = self._queue.next()
        # play the next song
        ctx.voice_client.play(source, after=lambda e: self.after_handle(ctx, error=e))

        # respond if possible
        if hasattr(source, 'title'):
            embed = Embed(title="Alright, here you go bro", description='[{}]({})'.format(source.title, source.url))
            self.now_playing_message = await ctx.send(embed=embed)

    @commands.command()
    async def queue(self, ctx, *, arg):
        async with ctx.typing():
            if URL.is_url(arg):
                source = await YTDLSource.from_url(arg, loop=self.bot.loop)
            else:
                source = await YTDLSource.from_query(arg, loop=self.bot.loop)
            self._queue.queue(source)

        # if it's the first item on the queue, just play right away, queue otherwise.
        if self._queue.queued() == 1 and not ctx.voice_client.is_playing():
            await self.ensure_voice(ctx)
            await self._play(ctx)
        else:
            last = self._queue.peek()
            # check if source has a title, for cases when the commands 'say' is invoked
            if hasattr(last, 'title'):
                embed = Embed(description="Alright bro, I queued [{}]({})".format(last.title, last.url))
                await ctx.send(embed=embed)

    @commands.command()
    async def next(self, ctx):
        if ctx.voice_client.is_playing():
            # stopping automatically invokes after_handle()
            ctx.voice_client.stop()

        # delete the "now playing" message
        if self.now_playing_message is not None:
            await self.now_playing_message.delete()

    def after_handle(self, ctx, *, error):
        coro = self._play(ctx)
        fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
        try:
            fut.result()
        except:
            pass

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
        queries = str(query).strip().split(" ")
        for q in queries:
            path = os.path.join(self.curr_audio_dir, "{}.mp3".format(q))
            if not os.path.exists(path):
                raise PathDoesNotExist(q)
        await self.ensure_voice(ctx)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Bro, you're not even on a voice channel")
                raise NotInChannel("You're not in a voice channel")