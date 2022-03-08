import discord
from discord import app_commands
from discord.ext import commands
from async_google_trans_new import AsyncTranslator
from async_google_trans_new.constant import LANGUAGES
from bot import MasterBot
from cogs.utils.help_utils import HelpSingleton
from static_embeds import lang_bed
from cogs.utils.cog import Cog


class Help(metaclass=HelpSingleton):
    def __init__(self, prefix):
        self.prefix = prefix

    def langs_help(self):
        message = f'`{self.prefix}languages`: Aliases: `langs` `codes`. Get the valid list of languages to translate to.'
        return message

    def trans_help(self):
        message = f'`{self.prefix}translate [language] <text>`: `language` is optional. Translate your text!\n' \
                  f'Examples: `{self.prefix}translate en 我蝙蝠侠也` or `{self.prefix}translate 我蝙蝠侠也`'
        return message

    def detect_help(self):
        message = f'`{self.prefix}detect <text>`: Detect what language the text is!'
        return message

    def full_help(self):
        help_list = [self.langs_help(), self.trans_help(), self.detect_help()]
        return '\n'.join(help_list)


class Translator(Cog, help_command=Help):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.translator = AsyncTranslator(url_suffix='com')
        print('Translator cog loaded')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.command is None:
            return
        if ctx.command.cog != self:
            return
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('Patience! Try again in {:.1f} seconds.'.format(error.retry_after))
        else:
            raise type(error)(error)

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def translate(self, ctx, lang=None, *, text=''):
        if lang in LANGUAGES.keys() or lang in LANGUAGES.values():
            if lang in LANGUAGES.values():
                lang = {v: k for k, v in LANGUAGES.items()}
        else:
            text = lang + ' ' + text
            lang = 'en'
        if not text:
            return await ctx.send('Give me something to translate.')
        result = await self.translator.translate(text=text, lang_tgt=lang)
        embed = discord.Embed(description=f'Original: {text}\nTranslated: {result}')
        embed.set_footer(text=f'Text successfully translated to {LANGUAGES.get(lang)}')
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def detect(self, ctx, *, text):
        result = await self.translator.detect(text)
        embed = discord.Embed(title=f'I detected the language as {result[1]}',
                              description=f'Text: {text}')
        embed.set_footer(text='Google translate did its best')
        await ctx.send(embed=embed)

    @detect.error
    async def error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Give me text.')
        else:
            raise error

    @commands.command(aliases=['codes', 'langs'])
    async def languages(self, ctx):
        await ctx.author.send(embed=lang_bed)

    @app_commands.command(name='translate', description='Translate using google translate!')
    @app_commands.describe(lang='The language to translate to. Use /languages for a list.')
    async def _translate(self, interaction, lang: str, text: str):
        if lang in LANGUAGES.keys() or lang in LANGUAGES.values():
            if lang in LANGUAGES.values():
                lang = {v: k for k, v in LANGUAGES.items()}
        else:
            await interaction.response.send_message('Use /languages for a valid list of languages.')
            return
        result = await self.translator.translate(text=text, lang_tgt=lang)
        embed = discord.Embed(description=f'Original: {text}\nTranslated: {result}')
        embed.set_footer(text=f'Text successfully translated to {LANGUAGES.get(lang)}')
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='languages', description='Get a valid list of languages.')
    async def _languages(self, interaction):
        await self.languages(interaction)
        await interaction.response.send_message('Check ur DMs')

    @app_commands.command(name='detect', description='Detect the language of your text.')
    @app_commands.describe(text='The text to detect the language of.')
    async def _detect(self, interaction, text: str):
        result = await self.translator.detect(text)
        embed = discord.Embed(title=f'I detected the language as {result[1]}',
                              description=f'Text: {text}')
        embed.set_footer(text='Google translate did its best')
        await interaction.response.send_message(embed=embed)

    #  the following commands cannot be used in a cog until context menus in cogs are supported
    # @app_commands.context_menu(name='detect')
    # async def __detect(self, interaction: discord.Interaction, message: discord.Message):
    #     await self._detect._callback(interaction, message.content)

    # @app_commands.context_menu(name='translate')
    # async def __translate(self, interaction: discord.Interaction, message: discord.Message):
    #     await self._translate._callback(interaction, message.content)


def setup(bot: MasterBot):
    Translator.setup(bot)
