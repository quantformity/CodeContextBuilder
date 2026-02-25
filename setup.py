from setuptools import setup, find_packages

setup(
    name="code-context-builder",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "tree-sitter>=0.23.0",
        "tree-sitter-python",
        "tree-sitter-go",
        "tree-sitter-java",
        "tree-sitter-typescript",
        "tree-sitter-cpp",
        "tree-sitter-c",
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
