#!/usr/bin/env python
from distutils.core import setup
from vctrl import __version__

setup(
    name="videocontrol",
    version=__version__,
    description="Video cueing board for live arts",
    author="Alexandre Quessy",
    author_email="alexandre@quessy.net",
    url="http://www.toonloop.com",
    packages=["vctrl"],
    scripts=["videocontrol"]
    )

