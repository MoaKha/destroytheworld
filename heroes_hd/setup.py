"""Setup script for Heroes HD."""
from setuptools import setup, find_packages

setup(
    name="heroes-hd",
    version="1.0.0",
    description="Heroes of Might & Magic III - HD Edition (Fan Recreation)",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pygame>=2.5.0",
        "numpy>=1.24.0",
        "noise>=1.2.2",
    ],
    entry_points={
        "console_scripts": [
            "heroes-hd=main:main",
        ],
    },
)
