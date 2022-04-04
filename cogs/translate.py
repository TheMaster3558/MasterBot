import discord
from discord import app_commands
from discord.ext import commands
from async_google_trans_new import AsyncTranslator
from async_google_trans_new.constant import LANGUAGES

from bot import MasterBot
from static_embeds import lang_bed
from cogs.utils.app_and_cogs import Cog


class Translator(Cog, name='translation'):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.translator = None
        print('Translator cog loaded')
    
    async def cog_load(self):
        await super().cog_load()
        self.translator = AsyncTranslator(url_suffix='com')
        self.bot.translator = self.translator  # for context menus

    async def cog_command_error(self, ctx, error):
        error: commands.CommandError

        if ctx.command is None:
            return
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('Patience! Try again in {:.1f} seconds.'.format(error.retry_after))
        else:
            await self.bot.on_command_error(ctx, error)

    @commands.command(description='I can translate text because im cool')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def translate(self, ctx, lang='', *, text=''):
        if lang in LANGUAGES.keys() or lang in LANGUAGES.values():
            if lang in LANGUAGES.values():
                lang = {v: k for k, v in LANGUAGES.items()}
        else:
            text = lang + ' ' + text
            lang = 'en'

        if not text or not any([char != ' ' for char in list(text)]):
            await ctx.send('Give me something to translate.')
            return

        result = await self.translator.translate(text=text, lang_tgt=lang)
        embed = discord.Embed()
        embed.add_field(name='Original', value=text)
        embed.add_field(name='Translated', value=result)
        embed.set_footer(text=f'Text successfully translated to {LANGUAGES.get(lang)}')
        await ctx.send(embed=embed)

    @commands.command(description='What language is that text?')
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

    @commands.command(aliases=['codes', 'langs'], description='Get a list of languages for language commands.')
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


@app_commands.context_menu()
async def translate(interaction: discord.Interaction, message: discord.Message):
    translator: AsyncTranslator = interaction.client.translator  # type: ignore

    result = await translator.translate(message.content, lang_tgt='en')
    embed = discord.Embed(description=f'Original: {message.content}\nTranslated: {result}')
    embed.set_footer(text='Text successfully translated to English')
    await interaction.response.send_message(embed=embed, ephemeral=True)


@app_commands.context_menu()
async def detect(interaction: discord.Interaction, message: discord.Message):
    translator: AsyncTranslator = interaction.client.translator  # type: ignore

    result = await translator.detect(message.content)
    embed = discord.Embed(title=f'I detected the language as {result[1]}',
                          description=f'Text: {message.content}')
    embed.set_footer(text='Google translate did its best')
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: MasterBot):
    await Translator.setup(bot)

    try:
        bot.tree.add_command(translate)
        bot.tree.add_command(detect)
    except app_commands.CommandAlreadyRegistered:
        pass
