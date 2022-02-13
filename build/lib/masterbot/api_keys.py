class MasterBotAPIKeyManager:
    def __init__(self, **keys):
        """A manager for api keys required for cogs
        **keys:
            clash_royale
            weather
        """
        self.keys = keys

    @property
    def clash_royale(self):
        return self.keys.get('clash_royale')

    @property
    def weather(self):
        return self.keys.get('weather')
