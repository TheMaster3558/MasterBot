class HelpSingleton(type):
    _instances = {}

    def __call__(cls, prefix, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(prefix, *args, **kwargs)
        cls._instances[cls].prefix = prefix
        return cls._instances[cls]



