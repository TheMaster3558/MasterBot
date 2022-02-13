from setuptools import setup


with open('requirements.txt', 'r') as r:
    requirements = r.read().splitlines()


with open('masterbot/__init__.py', 'r') as v:
    lines = v.read().splitlines()
    for line in lines:
        if line.startswith('__version__ = '):
            version = line[13:]
            break


packages = [
    'masterbot',
    'masterbot.cogs'
]


setup(name='masterbot',
      author='The Master',
      description='A discord bot made with discord.py',
      url='https://github.com/chawkk6404/MasterBot',
      install_requires=requirements,
      python_requires='>=3.10.0',
      version=version,
      packages=packages)
