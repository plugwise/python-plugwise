import codecs
import os.path

from setuptools import find_packages, setup


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="plugwise",
    version=get_version("plugwise/__init__.py"),
    description="Plugwise (Adam/Anna/P1/Stick/Stretch) API to use in conjunction with Home Assistant Core.",
    long_description="Plugwise API to use in conjunction with Home Assistant, but it can also be used as a python-module.",
    keywords="HomeAssistant HA Home Assistant Anna Adam P1 Smile Stretch Stick Plugwise",
    url="https://github.com/plugwise/python-plugwise",
    author="Plugwise-team",
    author_email="info@compa.nl",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "async_timeout<4.0",
        "crcmod",
        "defusedxml",
        "pyserial",
        "pytz",
        "python-dateutil",
        "semver",
    ],
    zip_safe=False,
)
