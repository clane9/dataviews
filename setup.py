import pathlib

from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()


def get_version():
    path = HERE / "dataviews" / "__init__.py"
    py = open(path, "r").readlines()
    version_line = [l.strip() for l in py if l.startswith("__version__")][0]
    version = version_line.split("=")[-1].strip().strip("'\"")
    return version


setup(
    name="dataviews",
    version=get_version(),
    author="Connor Lane",
    license="MIT",
    url="https://github.com/clane9/dataviews",
    description="Symbolic links + logic + multiple targets",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=["dataviews"],
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        "dill",
    ],
    extras_require={},
)
