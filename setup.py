from setuptools import setup, find_packages

setup(
    name="code-context-builder",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "tree-sitter==0.21.3",
        "tree-sitter-languages",
        "httpx",
        "python-dotenv",
        "click",
        "rich",
        "pathspec"
    ],
    entry_points={
        "console_scripts": [
            "ccb=ccb.cli:main",
        ],
    },
)
