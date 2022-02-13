"""
License: Apache License 2.0
2021-present The Master
See LICENSE for more
"""


import discord


class View(discord.ui.View):
    async def disable_all(self, message) -> None:
        for child in self.children:
            if not child.disabled:
                child.disabled = True
        await message.edit(view=self)

    async def disable_button(self, name, message) -> None:
        for child in self.children:
            if child.label == name:
                child.disabled = True
                break
        await message.edit(view=self)
