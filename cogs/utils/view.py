import discord
from typing import TypeVar


ItemT = TypeVar('ItemT', bound=discord.ui.Item)


async def smart_send(interaction: discord.Interaction, content=discord.utils.MISSING, **kwargs):
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
