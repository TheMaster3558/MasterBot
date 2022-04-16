"""
MasterBot
~~~~~~~~~~
a Discord Bot with many uses and more to come

:copyright: (c) 2021-present The Master
:license: Mozilla Public License Version 2.0, see LICENSE for more
"""


from __future__ import annotations

from time import perf_counter
from typing import Iterable, Any
import logging
import asyncio
import traceback
import sys
import warnings

import discord
from discord import app_commands
from discord.ext import commands
from cogs.utils.app_and_cogs import Cog, NoPrivateMessage

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, module="fuzzywuzzy")
    from fuzzywuzzy import fuzz


class MasterBotCommandTree(app_commands.CommandTree):
    async def on_error(
        self,
        interaction: discord.Interaction,
        command: app_commands.ContextMenu | app_commands.Command[Any, ..., Any] | None,
        error: app_commands.AppCommandError,
    ) -> None:
        if isinstance(error, NoPrivateMessage):
            await interaction.response.send_message("Try this in a server.")
            return
        traceback.print_exception(error, file=sys.stderr)


class MasterBot(commands.Bot):
    __version__ = "1.6.0"
    test_guild = discord.Object(id=878431847162466354)

    def __init__(
        self,
        cr_api_key: str,
        weather_api_key: str,
        mongo_db: str,
        /,
        *,
        token: str,
        **options,
    ) -> None:
        import monkeypatches

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        options["intents"] = intents

        super().__init__(**options)

        self.start_time = perf_counter()
        self.on_ready_time = None

        self.clash_royale = cr_api_key
        self.weather = weather_api_key
        self.token = token

        self.prefixes = {}
        self.prefixes_db = None
        self.moderation_mongo = mongo_db

        logger = logging.getLogger("discord")
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(
            filename="logs/discord.log", encoding="utf-8", mode="w"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
        )
        logger.addHandler(handler)

        self.locks: dict[Cog, asyncio.Lock] = {}

    @classmethod
    def default(
        cls, cr_api_key: str, weather_api_key: str, mongo_db: str, /, *, token: str
    ) -> MasterBot:
        """The default options"""
        return cls(
            cr_api_key,
            weather_api_key,
            mongo_db,
            command_prefix=commands.when_mentioned_or("!"),
            activity=discord.Game(f"version {cls.__version__}"),
            strip_after_prefix=True,
            enable_debug_events=True,
            token=token,
            tree_cls=MasterBotCommandTree,
        )

    def acquire_lock(self, cog: Cog) -> asyncio.Lock:
        if cog not in self.locks:
            self.locks[cog] = asyncio.Lock()
        return self.locks[cog]

    async def delete_app_commands(self) -> None:
        await self.http.bulk_upsert_global_commands(self.application_id, payload=[])

    async def load_extensions(self) -> None:
        cogs = (
            "cogs.clash_royale",
            "cogs.help_info",
            "cogs.code",
            "cogs.forms",
            "cogs.games",
            "cogs.botmath",
            "cogs.roles",
            "cogs.translate",
            "cogs.trivia",
            "cogs.webhook",
            "cogs.weather",
            "cogs.jokes",
            "cogs.version",
            "cogs.music",
            "cogs.chat"
        )
        await asyncio.gather(
            *(self.loop.create_task(self.load_extension(cog)) for cog in cogs)
        )

    async def setup_hook(self) -> None:
        self.loop.create_task(self.sync_once())
        await self.load_extensions()

    async def sync_once(self) -> None:
        # to make sure tree only gets synced once
        # put in setup hook
        await self.wait_until_ready()
        await self.tree.sync()

    async def on_ready(self) -> None:
        self.on_ready_time = perf_counter()
        print("Logged in as {0} ID: {0.id}".format(self.user))
        print(
            "Time taken to start up:",
            round(self.on_ready_time - self.start_time, 1),
            "seconds",
        )

    def possible_commands(
        self, context: commands.Context, ratio: int = 70
    ) -> list[str]:
        return [
            cmd
            for cmd in self.all_commands
            if fuzz.ratio(context.message.content, cmd) > ratio
        ]

    async def on_command_error(
        self, context: commands.Context, exception: commands.errors.CommandError
    ) -> None:
        if isinstance(exception, commands.CommandNotFound):
            possibles = self.possible_commands(context)
            if len(possibles) > 0:
                embed = discord.Embed(
                    title="I couldn't find that command",
                    description="Maybe you meant:\n`{}`".format("`\n`".join(possibles)),
                )
                await context.reply(embed=embed, mention_author=False)
            return

        traceback.print_exception(exception, file=sys.stderr)

    async def restart(self) -> None:
        """Reloads all extensions and clears the cache"""
        extensions = list(self.extensions).copy()
        for ext in extensions:
            await self.reload_extension(ext)
        self.clear()

    @property
    def oath_url(self) -> str | None:
        if not self.user:
            return None
        permissions = discord.Permissions(
            manage_roles=True,
            manage_channels=True,
            kick_members=True,
            ban_members=True,
            manage_webhooks=True,
            moderate_members=True,
            send_messages=True,
            add_reactions=True,
        )
        return discord.utils.oauth_url(
            self.user.id,
            permissions=permissions,
        )

    def custom_oath_url(
        self,
        permissions: discord.Permissions | None = None,
        scopes: Iterable[str] | None = None,
    ) -> str | None:
        if not self.user:
            return None
        return discord.utils.oauth_url(
            self.user.id, permissions=permissions, scopes=scopes
        )

    async def start(self, token: str = None, *, reconnect: bool = True) -> None:
        token = token or self.token
        await super().start(token, reconnect=reconnect)


def run_many(*instances: MasterBot):
    async def runner():
        loop = asyncio.get_event_loop()
        _log = logging.getLogger(__name__)

        _tasks = []

        for index, instance in enumerate(instances):
            try:
                _tasks.append(loop.create_task(instance.start()))
            except Exception as exc:
                _log.error(f"{instance} has failed to start", exc_info=exc)
            else:
                _log.info(f"{instance} has started")

        try:
            await asyncio.gather(*_tasks)
        except KeyboardInterrupt:
            return

    asyncio.run(runner())
