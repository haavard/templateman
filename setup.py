from setuptools import setup

setup(
    name="templateman",
    version="0.1",
    description="Create new files from templates interactively.",
    author="Håvard Pettersson",
    author_email="mail@haavard.me",
    url="https://github.com/haavardp/templateman",

    install_requires=[
        "Click",
        "Jinja2"
    ],

    packages=["templateman"],
    package_data={"templateman": ["templates/*"]},

    entry_points="""
        [console_scripts]
        templateman=templateman:main
    """
)
