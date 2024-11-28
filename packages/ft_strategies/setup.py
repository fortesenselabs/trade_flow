from setuptools import setup, find_packages

# Read requirements from requirements.txt
with open("requirements.txt", "r") as f:
    requirements = f.readlines()

setup(
    name="ft_strategies",
    version="0.1.0",
    packages=find_packages(include=["ft_strategies", "ft_strategies.*"]), 
    author="Fortesense Labs",
    author_email="fortesenselabs@gmail.com",
    install_requires=requirements,
)