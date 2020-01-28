import os

from setuptools import find_packages, setup

info = {}
version = os.path.join("llyfrau", "_version.py")

with open(version) as f:
    exec(f.read(), info)


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="llyfrau",
    version=info["__version__"],
    project_urls={
        "Source": "https://github.com/alcarney/llyfrau",
        "Tracker": "https://github.com/alcarney/llyfrau/issues",
    },
    description="Bookmark management",
    long_description=readme(),
    long_description_content_type="text/markdown",
    author="Alex Carney",
    author_email="alcarneyme@gmail.com",
    license="MIT",
    packages=find_packages(".", exclude=["tests"]),
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    entry_points={"console_scripts": ["llyfr = llyfrau.__main__:main"],},
)
