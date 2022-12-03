from setuptools import setup

setup(
    name="datocms",
    version="0.1.0",
    description="DatoCMS Python Library",
    keywords=["datocms"],
    author="Rostyslav Bohomaz",
    author_email="rostyslav.db@gmail.com",
    url="https://github.com/rostyq/python-datocms",
    packages=["datocms"],
    install_requires=["requests"],
    python_requires=">=3.11"
)
