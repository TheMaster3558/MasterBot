import discord
from discord.ext import commands
from async_google_trans_new import AsyncTranslator
from async_google_trans_new.constant import LANGUAGES
import slash_util
import traceback
from bot import MasterBot


class Help:
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


class Translator(slash_util.ApplicationCog):
    def __init__(self, bot: MasterBot):
        super().__init__(bot)
        self.translator = AsyncTranslator(url_suffix='com')
        print('Translator cog loaded')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.command is None:
            traceback.print_exception(error)
            return
        if ctx.command.cog != self:
            return
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send('Patience! Try again in {:.1f} seconds.'.format(error.retry_after))
        else:
            raise type(error)(error)

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def translate(self, ctx, lang, *, text):
        if lang in LANGUAGES.keys() or lang in LANGUAGES.values():
            if lang in LANGUAGES.values():
                lang = {v: k for k, v in LANGUAGES.items()}
        else:
            text = lang + ' ' + text
            lang = 'en'
        result = await self.translator.translate(text=text, lang_tgt=lang)
        embed = discord.Embed(description=f'Original: {text}\nTranslated: {result}')
        embed.set_footer(text=f'Text successfully translated to {LANGUAGES.get(lang)}')
        await ctx.send(embed=embed)

    @translate.error
    async def error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
        else:
            raise type(error)(error)

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
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
        else:
            raise type(error)(error)

    @commands.command(aliases=['codes', 'langs'])
    async def languages(self, ctx):
        embed = discord.Embed(title='List of Languages',
                              description='\n'.join(f'{k}/{v}' for k, v in LANGUAGES.items()))
        await ctx.author.send(embed=embed)

    @slash_util.slash_command(name='translate', description='Translate using google translate!')
    @slash_util.describe(lang='The language to translate to. Use /languages for a list.')
    async def _translate(self, ctx, lang: str, text: str):
        if lang in LANGUAGES.keys() or lang in LANGUAGES.values():
            if lang in LANGUAGES.values():
                lang = {v: k for k, v in LANGUAGES.items()}
        else:
            return await ctx.send('Use /languages for a valid list of languages.')
        result = await self.translator.translate(text=text, lang_tgt=lang)
        embed = discord.Embed(description=f'Original: {text}\nTranslated: {result}')
        embed.set_footer(text=f'Text successfully translated to {LANGUAGES.get(lang)}')
        await ctx.send(embed=embed)

    @slash_util.slash_command(name='languages', description='Get a valid list of languages.')
    async def _languages(self, ctx):
        await self.languages(ctx)

    @slash_util.slash_command(name='detect', description='Detect the language of your text.')
    @slash_util.describe(text='The text to detect the language of.')
    async def _detect(self, ctx, text: str):
        await self.detect(ctx, text)


def setup(bot: commands.Bot):
    bot.add_cog(Translator(bot))
