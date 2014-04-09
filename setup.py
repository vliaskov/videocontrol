#!/usr/bin/env python
from distutils.core import setup

__version__ = "0.1.1"

setup(
    name="toonplayer",
    version=__version__,
    description="The Toonplayer Looping Video Player",
    author="Alexandre Quessy",
    author_email="alexandre@quessy.net",
    url="http://www.toonloop.com",
    packages=["toonplay"],
    scripts=["toonplayer"]
    )
