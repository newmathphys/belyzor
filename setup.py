#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="belarus-etalon-2",
    version="1.0.0",
    author="BelEton-2 Team",
    description="Інтэлектуальная пошукавая сістэма па гісторыі Беларусі",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/belarus-etalon-2",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    install_requires=[
        "numpy",
    ],
    extras_require={
        "dev": ["pytest", "sentence-transformers"],
    },
    python_requires='>=3.8',
    entry_points={
        "console_scripts": [
            "belarus-etalon=src.core.ultimate_engine_v1:main",
        ],
    },
)
