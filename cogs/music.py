from __future__ import annotations


import discord
from discord import app_commands
from discord.ext import commands
import wavelink
from cogs.utils.app_and_cogs import Cog, command
from bot import MasterBot
import asyncio
from cogs.utils.view import View


def humanize_time(seconds: int | float) -> str:
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    if len(str(remaining_seconds)) == 1:
        remaining_seconds = '0' + str(remaining_seconds)
    return f'{minutes}:{remaining_seconds}'


class SongView(View):
    def __init__(self, player: Player, *, loop: asyncio.AbstractEventLoop):
        super().__init__(timeout=None)
        self.player = player
        self.loop = loop

    @discord.ui.button(emoji='\u23f8', style=discord.ButtonStyle.primary, custom_id='0')
    async def play_or_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Done.', ephemeral=True)

        if button.custom_id == '0':
            self.loop.create_task(self.player.pause())
            button.emoji = '▶'
            button.custom_id = '1'

        elif button.custom_id == '1':
            self.loop.create_task(self.player.resume())
            button.emoji = '⏸'
            button.custom_id = '0'

        await interaction.message.edit(view=self)

    @discord.ui.button(emoji='⏭', style=discord.ButtonStyle.primary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Skipping...', ephemeral=True)
        await self.player.force_next()

    @discord.ui.button(label='Leave', style=discord.ButtonStyle.danger)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.disconnect(force=True)
        await interaction.response.send_message('Bye.', ephemeral=True)
        await self.disable_all(interaction.message)
        del self.player.cog.queues[interaction.guild_id]
        self.stop()


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client: MasterBot
        self.cog: Music = self.client.get_cog('music')  # type: ignore

        self.message: discord.Message = None  # type: ignore

        self.queue: asyncio.Queue = None  # type: ignore
        self._event = asyncio.Event()
        self.started = False
        self._first_iteration = True
        self._waiting_task: asyncio.Task = None  # type: ignore
        self.current: wavelink.Track = None  # type: ignore

    async def make_embed(self, edit: bool = True) -> discord.Embed:
        track: wavelink.Track = self.current

        embed = discord.Embed(title=track.title)
        embed.add_field(name='Artist', value=track.author)
        embed.add_field(name='Duration', value=humanize_time(track.duration))
        if edit:
            await self.message.edit(embed=embed)
        return embed

    async def wait_until_song_finished(self):
        await self._event.wait()

    async def play(
        self, source: wavelink.abc.Playable, replace: bool = True, start: int = 0, end: int = 0
    ):
        await super().play(source=source, replace=replace, start=start, end=end)
        self._event.clear()

        async def sleep():
            await asyncio.sleep(source.duration)
            self._event.set()

        self._waiting_task = self.client.loop.create_task(sleep())

    async def force_next(self):
        self._event.set()
        self._waiting_task.cancel()
        await self.pause()

    async def _consume_queue(self):
        self.queue = self.cog.queues[self.channel.guild.id]

        while True:
            search: wavelink.Track = await self.queue.get()
            self.current = search

            if not self._first_iteration:
                await self.make_embed()
                await self.message.reply(f'Now playing "{self.current.title}"')

            await self.play(search)
            await self.wait_until_song_finished()
            self._first_iteration = False

    def start(self):
        if not self.started:
            def leave(*args):
                self.client.loop.create_task(self.disconnect(force=True))

            f = asyncio.ensure_future(self._consume_queue(), loop=self.client.loop)
            f.add_done_callback(leave)

            self.started = True


class Music(Cog, name='music'):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.queues: dict[int, asyncio.Queue[wavelink.Track]] = {}
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

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await guild.create_voice_channel(name='Join to create room!')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if after.channel and after.channel.name == 'Join to create room!':
            channel = await member.guild.create_voice_channel(name=f"{member.display_avatar}'s room")
            await member.move_to(channel, reason='Private room creation')
            return

        if not before.channel:
            return

        if before.channel.name.endswith("'s room") and len(before.channel.members) < 1:
            await before.channel.delete(reason='All members left')

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

        self.queues[ctx.guild.id] = asyncio.Queue()

        vc.start()

        await ctx.send(f'Joined {vc.channel.mention}')

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, search: wavelink.SoundCloudTrack):
        if not ctx.author.voice:
            await ctx.send('Join a voice channel.')
            return

        elif not ctx.voice_client:
            vc: Player = await ctx.author.voice.channel.connect(cls=Player)  # type: ignore

        else:
            vc: Player = ctx.voice_client  # type: ignore

        self.queues[ctx.guild.id].put_nowait(search)

        await asyncio.sleep(0)

        if not vc.message:
            view = SongView(vc, loop=self.bot.loop)

            embed = await vc.make_embed(edit=False)
            msg = await ctx.send(embed=embed, view=view)
            vc.message = msg
        else:
            await ctx.send(f'"{search.title}" added to queue.')


async def setup(bot: MasterBot):
    await Music.setup(bot)
