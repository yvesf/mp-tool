#!/usr/bin/env python3
from setuptools import setup

setup(name='mp-tool',
      version='0.1',
      description='CLI tool to interact with micropython webrepl',
      author='Yves Fischer',
      author_email='yvesf+git@xapek.org',
      license="MIT",
      packages=['mp_tool'],
      scripts=['mp-tool'],
      url='https://example.com/',
      install_requires=['websocket_client==0.40.0','pyserial==3.2.1'],
      tests_require=[],
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
      ])
