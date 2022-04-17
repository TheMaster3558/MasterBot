from __future__ import annotations

import asyncio
from concurrent.futures import TimeoutError
from typing import Optional, TYPE_CHECKING
import os as __os__
import sys as __sys__
import builtins
import io
import threading

import discord
from discord import app_commands
from discord.ext import commands
import aiofiles

from cogs.utils.app_and_cogs import Cog

if TYPE_CHECKING:
    from bot import MasterBot

    # bot.py uses EventLoopThread


class EventLoopThread(threading.Thread):
    def __init__(self, *args, loop: asyncio.AbstractEventLoop = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop = loop or asyncio.new_event_loop()
        self.running = False

    def run(self):
        self.running = True
        self.loop.run_forever()

    def run_coro(self, coro, timeout: int | None = None):
        return asyncio.run_coroutine_threadsafe(coro, loop=self.loop).result(
            timeout=timeout
        )

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.join()
        self.running = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# print to the string io instead of the console only locally


async def aexec(code, string_io: io.StringIO):
    # https://stackoverflow.com/questions/44859165/async-exec-in-python
    # Make an async function with the code and `exec` it

    def string_io_print(*args, **kwargs):
        kwargs["file"] = string_io
        print(*args, **kwargs)

    _globals = vars(builtins).copy()
    _globals["print"] = string_io_print

    exec(
        f"async def __ex(): " + "".join(f"\n {l}" for l in code.split("\n")),
        _globals,
        locals(),
    )
    # Get `__ex` from local variables, call it and return the result
    return await locals()["__ex"]()


class CodeBlock:
    """Credits to Rapptz the creator of RoboDanny"""

    missing_error = "Missing code block. Please use the following markdown\n\\`\\`\\`py\ncode here\n\\`\\`\\`"

    def __init__(self, argument):
        try:
            block, code = argument.split("\n", 1)
        except ValueError:
            raise commands.BadArgument(self.missing_error)

        if not block.startswith("```") and not code.endswith("```"):
            raise commands.BadArgument(self.missing_error)
        self.source = code.rstrip("`").replace("```", "")


class SlashCodeBlock:
    def __init__(self, argument):
        self.source = argument


class Code(Cog, name="code"):
    """
    Many of the commands are owner only
    """

    forbidden_imports = [
        "sys",
        "subprocess",
        "setuptools",
        "distutils",
        "threading",
        "multiprocessing",
        "Cython",
        "aioconsole",
        "gc",
    ]
    forbidden_words = ["ctx", "__os__", "__sys__", "self", "open(", "eval(", "exec"]

    def __init__(self, bot: MasterBot):
        super().__init__(bot)

        self.created_mentions = discord.AllowedMentions(users=False)

        print("Code cog loaded")

    async def cog_command_error(self, ctx: commands.Context, error):
        error: commands.CommandError

        if not ctx.command:
            return
        if ctx.command.has_error_handler():
            return
        if isinstance(
            error,
            (
                commands.MissingPermissions,
                commands.MissingRequiredArgument,
                commands.NotOwner,
            ),
        ):
            return
        else:
            if not ctx.command.has_error_handler():
                await self.bot.on_command_error(ctx, error)

    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.command(name="eval", description="Evaluate some python code.")
    async def _eval(self, ctx, *, code: CodeBlock | SlashCodeBlock):
        """
        This command will need lots of working on.
        """
        async with ctx.typing():
            if len(code.source.split("\n")) > 300:
                await ctx.send("You can't eval over 300 lines.")
                return
            if any([word in code.source for word in self.forbidden_words]):
                await ctx.send("Your code has a word that would be risky to eval.")
                return

            temp_out = io.StringIO()

            try:
                try:
                    with EventLoopThread() as thr:
                        await asyncio.to_thread(
                            thr.run_coro, aexec(code.source, temp_out), 60
                        )
                        # to prevent blocking event loop if they use time.sleep etc
                except TimeoutError:
                    await ctx.reply("Your code took too long to run.")
                    return
            except Exception as e:
                await ctx.reply(
                    f"Your code raised an exception\n```\n{e.__class__.__name__}: {e}\n```"
                )
                return

            value = temp_out.getvalue()

            value = value or "No output"
            await ctx.reply(f"```\n{value}\n```")

            temp_out.close()

    @_eval.error
    async def error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            if await self.bot.is_owner(ctx.author):
                await ctx.reinvoke()
                return
            await ctx.send("Patience. Wait {:.1f} seconds".format(error.retry_after))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(str(error))
        else:
            await ctx.send("Command raised an exception\n```\n{}\n```".format(error))

    @commands.command(description="Check if a user can run a command")
    async def canrun(self, ctx, user: Optional[discord.User], *, command_name):
        _command: commands.Group | commands.Command = self.bot.all_commands.get(
            command_name
        )

        if _command is None:
            embed = discord.Embed(title=f"Command `{command_name}` not found.")
            await ctx.send(embed=embed)
            return

        ctx.author = user or ctx.author
        await _command.can_run(ctx)
        await ctx.send(f"{user} can run this command!")

    @canrun.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(title="Your too weak!", description=str(error))
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Missing something",
                description=f"`{self.bot.command_prefix}canrun [user] <command>`",
            )
            await ctx.send(embed=embed)
        elif isinstance(error, (commands.MemberNotFound, commands.UserNotFound)):
            await ctx.send("I couldn't find that person =(")
        else:
            raise error

    @commands.command(hidden=True)
    @commands.is_owner()
    async def logger(self, ctx, last=5):
        with aiofiles.open("logs/discord.log", "r") as l:
            log = await l.read()
        log = log.split("\n")
        log.reverse()
        full = [log[i] for i in range(1, last)]
        legnth = [i for i in range(len(log) - last, len(log))]
        lined = "\n".join(f"Line {legnth[i]}: {full[i]}" for i in range(len(full)))
        await ctx.send("```\n{}\n```".format(lined))

    @commands.command(name="os", hidden=True)
    @commands.is_owner()
    async def _os(self, ctx, *, what):
        await asyncio.to_thread(__os__.system, what)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def close(self, ctx):
        await ctx.send("Closing. Bye bye!")
        await self.bot.close()
        __sys__.exit()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *exts):
        for ext in exts:
            await self.bot.reload_extension(f"cogs.{ext}")
        await ctx.send(f'Extensions reloaded: {", ".join(exts)}')

    @commands.command(hidden=True)
    async def load(self, ctx, *exts):
        for ext in exts:
            await self.bot.load_extension(f"cogs.{ext}")
        await ctx.send(f'Extensions loaded: {", ".join(exts)}')

    @commands.command(hidden=True)
    async def unload(self, ctx, *exts):
        for ext in exts:
            await self.bot.unload_extension(f"cogs.{ext}")
        await ctx.send(f'Extensions unloaded: {", ".join(exts)}')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx):
        """Nearly a full restart. Just without restarting the connection."""
        await ctx.send("Ok!")
        try:
            await self.bot.restart()
        except Exception as exc:
            await ctx.send(f"An Error!?\n```\n{exc}\n```")

    @commands.group(hidden=True)
    async def git(self, ctx):
        pass

    @git.command(hidden=True)
    @commands.is_owner()
    async def add(self, ctx, path):
        await asyncio.to_thread(__os__.system, "git add {}".format(path))
        await ctx.send("Files in {} were added to the next commit.".format(path))

    @git.command(hidden=True)
    @commands.is_owner()
    async def commit(self, ctx, *, message):
        await asyncio.to_thread(__os__.system, 'git commit -m "{}"'.format(message))
        await ctx.send(
            "Changes have been committed with the messageg {}".format(message)
        )

    @git.command(hidden=True)
    @commands.is_owner()
    async def push(self, ctx, force=False):
        _command = "git push"
        if force == "force":
            _command += " -f"
        await asyncio.to_thread(__os__.system, _command)
        await ctx.send("Files pushed. Force push = {}.".format(force == "force"))

    @commands.command(name="code", description="Get some code of the bot.")
    async def _code(self, ctx, file_path, lines=None):
        if any(name in file_path for name in ("main.py", "databases/", "venv/")):
            return

        if lines is None:
            pass
        elif "-" in lines:
            lines = [int(line) for line in lines.split("-")]
        else:
            lines = int(lines)

        try:
            async with aiofiles.open(file_path, "r") as file:
                content = (await file.read()).split("\n")
        except FileNotFoundError:
            await ctx.send("I " "couldn't find that file.")
            return
        if isinstance(lines, list):
            content = "\n".join(content[lines[0] + 1 : lines[1] + 1])
        elif lines is None:
            content = "\n".join(content)
        else:
            content = content[lines]

        content = content.replace("`", r"\`")
        try:
            embed = discord.Embed(
                title=f"Code for {file_path}", description=f"```py\n{content}\n```"
            )
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Too much to send.")

    @_code.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('You forgot "{}"'.format(error.param))
        else:
            raise error

    @app_commands.command(name="eval", description="Run a Python file")
    async def __eval(self, interaction: discord.Interaction, file: discord.Attachment):
        if not file.filename.endswith(".py"):
            await interaction.response.send_message("It must be a `python` file.")
            return

        code = await file.read()
        code = SlashCodeBlock(code.decode("utf-8"))

        if len(code.source.split("\n")) > 300:
            await interaction.response.send_message("You can't eval over 300 lines.")
            return
        if any([word in code.source for word in self.forbidden_words]):
            await interaction.response.send_message(
                "Your code has a word that would be risky to eval."
            )
            return
        if any(
            [
                f"import {word}" in code.source
                or f'__import__("{word}")' in code.source
                or f"__import__('{word}')" in code.source
                for word in self.forbidden_imports
            ]
        ):
            await interaction.response.send_message("You can't import that.")
            return

        await interaction.response.defer(thinking=True)

        temp_out = io.StringIO()

        try:
            try:
                with EventLoopThread() as thr:
                    await asyncio.to_thread(
                        thr.run_coro, aexec(code.source, temp_out), 60
                    )
                    # to prevent blocking event loop if they use time.sleep etc
            except TimeoutError:
                await interaction.followup.send("Your code took too long to run.")
                return
        except Exception as e:
            await interaction.followup.send(
                f"Your code raised an exception\n```\n{e.__class__.__name__!r}: {e}\n```"
            )
            return

        value = temp_out.getvalue()
        value = value or "No output"
        await interaction.followup.send(f"```\n{value}\n```")

        temp_out.close()

    @commands.command(hidden=True)
    async def sync(self, ctx, guild: bool = None):
        if guild:
            guild = self.bot.test_guild
        data = await self.bot.tree.sync(guild=guild)
        await ctx.send(data)

    @commands.command(description="Check when a user was created at.")
    async def created(self, ctx, user: discord.User | int):
        user = user.id if isinstance(user, discord.User) else user
        created_at = discord.utils.snowflake_time(user)
        timestamp = discord.utils.format_dt(created_at, "R")
        await ctx.reply(timestamp, mention_author=False)

    @created.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You need to give me a `user` or `id`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"I couldn't make that into a user or id")
        else:
            raise error

    @app_commands.command(
        name="created",
        description="See when a discord user or snowflake was created at",
    )
    @app_commands.describe(user="A discord user", snowflake="A discord ID")
    async def _created(
        self, interaction, user: discord.User = None, snowflake: int = None
    ):
        if not user and not snowflake:
            await interaction.response.send_message(
                "You must give a user or snowflake", ephemeral=True
            )
            return

        if not snowflake:
            snowflake = user.id

        created_at = discord.utils.snowflake_time(snowflake)
        timestamp = discord.utils.format_dt(created_at, "R")

        if user:
            timestamp = f"{user.mention} was created " + timestamp
        elif snowflake:
            timestamp = f"{snowflake} was created " + timestamp

        await interaction.response.send_message(
            timestamp, allowed_mentions=self.created_mentions
        )

    @commands.command(description="Get the binary of a number.")
    async def binaryint(self, ctx, integer: int):
        await ctx.send(f"{integer:b}")

    @commands.command(aliases=["hexadecimal"], description="Get the hex of a number.")
    async def hexint(self, ctx, integer: int):
        await ctx.send(str(hex(integer)))

    @commands.command(aliases=["octal"], description="Get the octal of a number.")
    async def octint(self, ctx, integer: int):
        await ctx.send(str(oct(integer)))

    @binaryint.error
    @hexint.error
    @octint.error
    async def error(self, ctx, error):
        await ctx.send(str(error))


async def setup(bot: MasterBot):
    await Code.setup(bot)
