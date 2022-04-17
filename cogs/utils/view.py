# -*- coding: utf-8 -*-

from typing import TypeVar

import discord


ItemT = TypeVar("ItemT", bound=discord.ui.Item)


async def smart_send(
    interaction: discord.Interaction, content=discord.utils.MISSING, **kwargs
):
    if interaction.response.is_done():
        return await interaction.followup.send(content=content, **kwargs)
    return await interaction.response.send_message(content=content, **kwargs)


class View(discord.ui.View):
    async def disable_all(self, message) -> None:
        for child in self.children:
            if not child.disabled:
                child.disabled = True
        await message.edit(view=self)

    async def disable_button(self, name, message) -> None:
        for child in self.children:
            if child.label == name:  # type: ignore
                child.disabled = True
                break
        await message.edit(view=self)

    def add_item(self, item: ItemT) -> ItemT:
        super().add_item(item)
        return item


MISSING = discord.utils.MISSING


class Paginator(View):
    def __init__(self, pages: list[discord.Embed], *, timeout: float = 180):
        self.pages = pages
        self.current_page: int = 0
        super().__init__(timeout=timeout)

        self.message: discord.Message = MISSING
        self.embed: discord.Embed = MISSING

    def configure_message(
        self, message: discord.Message, embed: discord.Embed | None = None
    ):
        embed = embed or message.embeds[0]

        self.message = message
        self.embed = embed

    async def send(self, channel: discord.TextChannel):
        self.embed = self.pages[self.current_page]
        self.message = await channel.send(embed=self.embed, view=self)

        await self.wait()
        await self.disable_all(self.message)

    @discord.ui.button(emoji="⬅", style=discord.ButtonStyle.primary)
    async def left(self, interaction: discord.Interaction, button):
        self.current_page -= 1

        if self.current_page < 0:
            self.current_page = len(self.pages) - 1

        self.embed = self.pages[self.current_page]
        await self.message.edit(embed=self.embed)
        await interaction.response.defer()

    @discord.ui.button(emoji="➡", style=discord.ButtonStyle.primary)
    async def right(self, interaction: discord.Interaction, button):
        self.current_page += 1

        if self.current_page >= len(self.pages):
            self.current_page = 0

        self.embed = self.pages[self.current_page]
        await self.message.edit(embed=self.embed)
        await interaction.response.defer()
