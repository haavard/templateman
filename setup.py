from setuptools import setup

setup(
    name="templateman",
    version="0.1",
    description="Create new files from templates interactively.",
    author="Håvard Pettersson",
    author_email="mail@haavard.me",
    url="https://github.com/haavardp/templateman",
    classifiers=[
        "License :: OSI Approved :: ISC License (ISCL)",
        "Topic :: Software Development",
        "Environment :: Console",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],

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
