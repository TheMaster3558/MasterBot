"""
License: Apache License 2.0
2021-present The Master
See LICENSE for more
"""


class MasterBotAPIKeyManager:
    def __init__(self, **keys):
        """A manager for api keys required for cogs
        **keys:
            clash_royale: https://developer.clashroyale.com/
            weather: https://www.weatherapi.com/
        """
        self.keys = keys

    @property
    def clash_royale(self):
        return self.keys.get('clash_royale')

    @property
    def weather(self):
        return self.keys.get('weather')
