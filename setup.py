#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="arxiv",
    version="0.0.0",
    author="Daniel Foreman-Mackey",
    author_email="danfm@nyu.edu",
    url="http://www.arxiv.io",
    packages=["arxiv"],
    package_data={"arxiv": ["*.txt", "templates/*", "static/*"]},
    include_package_data=True,
)
