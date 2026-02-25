# Code Context Builder (CCB) 🛠️🤖

**Code Context Builder** is a high-performance architectural mapping tool designed to transform complex codebases into "AI-ready" environments. It acts as a bridge between raw source code and coding agents (like Gemini, Claude, and GPT) by generating a **Distributed Context System**—a network of structured Markdown files that live alongside the code.

---

## 🌟 Features

- **Distributed Indexing**: Generates a `.context.md` in every directory summarizing its public symbols.
- **Agent Instructions**: Automatically adds guidance to the project root to teach agents how to maintain the index.
- **Multi-Language Support**: Robust parsing for **Python, Go, Java, TypeScript/JS, C/C++, and CUDA**.
- **LLM-Powered Summaries**: Automatically generates 1-2 sentence intent summaries for undocumented code using **Gemini, Claude, OpenAI, or Ollama**.
- **Incremental Scanning**: Uses SHA-256 hashing to only process changed files, saving time and LLM tokens.
- **Pip Installable**: Easy to install and use as a global CLI tool.

---

## 🚀 Installation

### From Source
1. Clone this repository.
2. Install the package in editable mode:
```bash
pip install -e .
```

### Dependencies
The tool requires Python 3.10+ and uses `tree-sitter` for high-accuracy parsing.

---

## ⚙️ Configuration

### Easy Setup
You can configure CCB interactively by running:
```bash
ccb init
```
This will create a `.ccbenv` file in your directory.

### Manual Configuration
CCB looks for a `.ccbenv` file in your project root.

```bash
# LLM Provider: gemini, claude, openai, ollama, lmstudio, llamacpp
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
LLM_API_KEY=your_google_api_key

# Optional: Custom output name
OUTPUT_FILE_NAME=.context.md
```

---

## 📖 Usage

### Scan a Codebase
Run the scanner on your current directory or a specific path:
```bash
ccb scan .
```

### Cleanup
To remove all generated `.context.md` files and the indexing cache:
```bash
ccb clean .
```

### What happens?
1. **Registry Check**: CCB checks `.code-index/registry.json` to see which files have changed.
2. **Parsing**: New/changed files are parsed using Tree-sitter to extract public classes and functions.
3. **Summarization**: Public symbols without documentation are summarized by your configured LLM.
4. **Markdown Generation**: `.context.md` files are created/updated in every folder.
5. **Root Context**: A project-level `.context.md` is created with instructions for any AI agents working on the repo.

---

## 🤖 How Agents Use CCB

When a coding agent "enters" your repository, it will find `.context.md` files. This allows the agent to:
- **Discover**: Quickly see what public methods are available in a module without reading the implementation.
- **Reuse**: Find existing utility functions instead of rewriting them.
- **Maintain**: The agent is instructed to update the `.context.md` whenever it modifies the public API, keeping the documentation "alive."

---

## 🛠️ Supported Languages

| Language | Public Symbol Detection Logic |
| :--- | :--- |
| **Python** | Non-underscored functions and classes. |
| **Go** | Exported symbols (Uppercase names). |
| **Java** | Symbols with the `public` modifier. |
| **TypeScript/JS** | Symbols with the `export` keyword. |
| **C/C++/CUDA** | Non-static symbols in headers and source files. |

---

## 🤝 Contributing

To add support for a new language:
1. Create a specialized logic in `ccb/parsers/universal.py` or a new parser class.
2. Register the extension in `ccb/core.py`.
