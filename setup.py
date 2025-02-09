from setuptools import setup

# with open("README.md", encoding="UTF-8") as f:
#     long_desc = f.read()

setup(
    name='pokeformance',
    description='Profile each line of a python file',
    # long_description=long_desc,
    # long_description_content_type="text/markdown",
    version='1',
    py_modules=['pokeformance'],
    entry_points='''
        [console_scripts]
        pokeformance=pokeformance:pokeformance
    ''',
    # url='https://github.com/pokepetter/ursina',
    author='Petter Amland',
    author_email='pokepetter@gmail.com',
    python_requires='>=3.8',
)
