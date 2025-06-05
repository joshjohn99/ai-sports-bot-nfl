from setuptools import setup, find_packages

setup(
    name="sports_bot",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "sqlalchemy>=2.0.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "rich>=13.0.0",
    ],
    python_requires=">=3.8",
) 