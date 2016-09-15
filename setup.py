"""
@author: dhoomakethu
"""

from setuptools import setup
from apocalypse import __version__
import platform

PSUTIL_ALPINE_LINUX = "4.1.0"

long_description = None
with (open('README.md')) as readme:
    long_description = readme.read()


def fix_ps_util(install_requires):
    for i, req in enumerate(install_requires[:]):
        if "psutil" in req:
            req = req.split("==")
            req[-1] = PSUTIL_ALPINE_LINUX
            req = "==".join(req)
            install_requires[i] = req

with open('requirements.txt') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n')
        if (line and not line.startswith('--'))
    ]
    if platform.system() == "Linux":
        fix_ps_util(install_requires)

setup(name="apocalypse",
      url='https://github.com/dhoomakethu/apocalypse',
      version=__version__,
      packages=['apocalypse', 'apocalypse.utils',
                'apocalypse.chaos', 'apocalypse.app', 'apocalypse.chaos.events',
                'apocalypse.exceptions', "apocalypse.server"],
      description="Introduce chaos on to docker ecosystem",
      long_description=long_description,
      author="dhoomakethu",
      author_email="otlasanju@gmail.com",
      install_requires=install_requires,
      scripts=['doom'],
      include_package_data=True,
      # dependency_links=['https://github.com/dhoomakethu/python-coloredlogs'
      #                   '/tarball/master#egg=python-coloredlogs-5.0.1']
)
