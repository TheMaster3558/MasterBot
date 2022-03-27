from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
import wavelink
from cogs.utils.app_and_cogs import Cog, command
from bot import MasterBot
import asyncio


def humanize_seconds(seconds: int | float) -> str:
    minutes = seconds // 60
    remaining_seconds = int()
    return f'{minutes}:{remaining_seconds}'


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client: MasterBot
        self.cog: Music = self.client.get_cog('music')  # type: ignore

        self.queue = None
        self._event = asyncio.Event()

    async def wait_until_song_finished(self):
        await self._event.wait()

    async def play(
        self, source: wavelink.abc.Playable, replace: bool = True, start: int = 0, end: int = 0
    ):
        await super().play(source=source, replace=replace, start=start, end=end)
        self._event.clear()

        await asyncio.sleep(source.duration)
        self._event.set()

    async def _eat_queue(self):
        self.queue = self.cog.queues[self.channel.guild.id]

        while True:
            source = await self.queue.get()
            await self.play(source)
            await self.wait_until_song_finished()

    def start(self):
        def leave():
            self.client.loop.create_task(self.disconnect(force=True))

        f = asyncio.ensure_future(self._eat_queue(), loop=self.client.loop)
        f.add_done_callback(leave)


class Music(Cog, name='music'):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.queues: dict[int, asyncio.Queue[wavelink.SoundCloudTrack]] = {}
        print('Music cog loaded')

    async def cog_load(self):
        await super().cog_load()
        self.bot.loop.create_task(self.connect())

    async def connect(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(bot=self.bot,
                                            host='losingtime.dpaste.org',
                                            port=2124,
                                            password='SleepingOnTrains')

    @commands.command(aliases=['j'])
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        if ctx.voice_client:
            await ctx.send("I'm already in a voice channel.")
            return

        if channel is not None:
            vc: Player = await channel.connect(cls=Player)  # type: ignore

        elif ctx.author.voice:
            vc: Playerawait = await ctx.author.voice.channel.connect(cls=Player)  # type: ignore

        else:
            await ctx.send('You must be in a channel or give me a voice channel. How else would I know where to join?')
            return

        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = asyncio.Queue()

        vc.start()

        await ctx.send(f'Joined {vc.channel.mention}')

    @commands.command(aliases=['dis'])
    async def leave(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.send("I'm not in a voice channel.")
            return

        await ctx.voice_client.disconnect(force=False)

        try:
            del self.queues[ctx.guild.id]
        except KeyError:
            pass

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, search: wavelink.SoundCloudTrack):
        if not ctx.voice_client:
            vc: Player = await ctx.author.voice.channel.connect(cls=Player)  # type: ignore

        elif not ctx.author.voice:
            await ctx.send('Join a voice channel first.')
            return

        else:
            vc: Player = ctx.voice_client  # type: ignore

        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = asyncio.Queue()

        vc.start()

        self.queues[ctx.guild.id].put_nowait(search)

        embed = discord.Embed(title=f'Now playing {search.title}')
        embed.add_field(name='Artist', value=search.author)
        embed.add_field(name='Duration', value=humanize_seconds(search.duration))

        await ctx.send(embed=embed)


async def setup(bot: MasterBot):
    await Music.setup(bot)





