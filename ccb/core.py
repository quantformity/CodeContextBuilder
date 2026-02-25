import os
import hashlib
import json
import pathlib
import re
from typing import Dict, List, Set
from .config import config
from .parsers.universal import UniversalParser
from .llm.ollama import OllamaProvider
from .llm.openai import OpenAIProvider

class Scanner:
    def __init__(self):
        self.parsers = [
            UniversalParser('python', ['.py']),
            UniversalParser('go', ['.go']),
            UniversalParser('java', ['.java']),
            UniversalParser('typescript', ['.ts', '.tsx', '.js', '.jsx']),
            UniversalParser('cpp', ['.cpp', '.hpp', '.cc', '.cxx', '.cu', '.cuh']),
            UniversalParser('c', ['.c', '.h']),
        ]
        self.registry_path = pathlib.Path(".code-index/registry.json")
        self.registry = self._load_registry()
        
        if config.llm.provider == "openai" or config.llm.provider in ["lmstudio", "llamacpp"]:
            self.llm = OpenAIProvider()
        else:
            self.llm = OllamaProvider()

    def _load_registry(self):
        if self.registry_path.exists():
            with open(self.registry_path, "r") as f:
                try:
                    return json.load(f)
                except:
                    return {"files": {}}
        return {"files": {}}

    def _save_registry(self):
        self.registry_path.parent.mkdir(exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self.registry, f, indent=2)

    def get_hash(self, content: str):
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def scan(self, root_dir: str):
        root = pathlib.Path(root_dir)
        files_to_scan = []
        extensions = [".py", ".go", ".java", ".ts", ".js", ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp", ".cu", ".cuh"]
        
        for ext in extensions:
            files_to_scan.extend(root.rglob(f"*{ext}"))

        contexts_by_folder = {}
        folder_dependencies: Dict[str, Set[str]] = {}
        all_public_symbols: Set[str] = set()

        # Pass 1: Parse and Registry Update
        for file_path in files_to_scan:
            rel_path = str(file_path.relative_to(root))
            if any(part.startswith('.') or part in ['node_modules', 'dist', 'build'] for part in file_path.parts):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except:
                continue
            
            file_hash = self.get_hash(content)
            cached = self.registry["files"].get(rel_path)

            folder = str(file_path.parent.relative_to(root))
            if folder not in folder_dependencies: folder_dependencies[folder] = set()
            self._extract_dependencies(content, folder_dependencies[folder])

            if cached and cached["hash"] == file_hash:
                symbols = cached["symbols"]
            else:
                parser = next((p for p in self.parsers if p.supports(file_path.suffix)), None)
                if not parser: continue
                
                print(f"Scanning {rel_path}...")
                try:
                    raw_symbols = parser.parse(content, rel_path)
                    symbols = [s.to_dict() for s in raw_symbols]

                    for s in symbols:
                        if not s.get("summary") and s.get("is_public"):
                            summary = self.llm.summarize(rel_path, s["code"])
                            if summary:
                                print(f"  Summarized {s['name']} via LLM.")
                                s["summary"] = summary
                    
                    self.registry["files"][rel_path] = {"hash": file_hash, "symbols": symbols}
                except Exception as e:
                    print(f"Error parsing {rel_path}: {e}")
                    continue

            # Accumulate all public symbol names for Pass 2 filtering
            for s in symbols:
                if s.get("is_public"):
                    all_public_symbols.add(s["name"])

            if folder not in contexts_by_folder: contexts_by_folder[folder] = []
            contexts_by_folder[folder].append({"path": rel_path, "symbols": symbols})

        # Pass 2: Filter 'calls' to only include internal public symbols
        for folder_contexts in contexts_by_folder.values():
            for ctx in folder_contexts:
                for s in ctx["symbols"]:
                    if s.get("calls"):
                        # Keep only calls that exist in our public registry
                        s["calls"] = sorted(list(set([c for d, c in zip(range(15), s["calls"]) if c in all_public_symbols and c != s["name"]])))

        self._save_registry()
        self._write_markdown(root, contexts_by_folder, folder_dependencies)

    def _extract_dependencies(self, content: str, deps: Set[str]):
        patterns = [
            r'^import\s+([\w\.]+)', 
            r'^from\s+([\w\.]+)\s+import', 
            r'^#include\s*[<"]([\w\./]+)[>"]', 
            r'^import\s+.*from\s+[\'"]([\w\./@\-]+)[\'"]', 
        ]
        for p in patterns:
            for match in re.finditer(p, content, re.MULTILINE):
                deps.add(match.group(1))

    def _write_markdown(self, root: pathlib.Path, contexts_by_folder: Dict, folder_deps: Dict[str, Set[str]]):
        for folder_rel, contexts in contexts_by_folder.items():
            if folder_rel == ".": continue
            
            md_path = root / folder_rel / config.output_file_name
            with open(md_path, "w") as f:
                f.write(f"# Directory: {folder_rel}\n\n")
                
                deps = sorted(list(folder_deps.get(folder_rel, set())))[:15]
                if deps:
                    f.write("## 📦 Dependencies\n")
                    f.write(", ".join([f"`{d}`" for d in deps]) + "\n\n")

                self._write_file_contexts(f, contexts)
            print(f"Updated {md_path}")

        root_md = root / config.output_file_name
        with open(root_md, "w") as f:
            f.write(f"# Project Root: {root.name}\n\n")
            f.write("## 🤖 Agent Instructions\n")
            f.write("This codebase uses a **Distributed Context System**.\n")
            f.write(f"1. Every folder contains a `{config.output_file_name}` summarizing its public API.\n")
            f.write(f"2. You MUST update these files when you change public symbols.\n\n")
            
            if "." in contexts_by_folder:
                f.write("## Root Level Files\n")
                self._write_file_contexts(f, contexts_by_folder["."])
        print(f"Updated Root Context: {root_md}")

    def _write_file_contexts(self, f, contexts):
        all_filenames = [os.path.basename(ctx['path']) for ctx in contexts]
        
        for ctx in contexts:
            fname = os.path.basename(ctx['path'])
            base, ext = os.path.splitext(fname)
            
            related = []
            if ext in ['.cpp', '.cc', '.c', '.cu']:
                for h_ext in ['.h', '.hpp', '.cuh']:
                    if f"{base}{h_ext}" in all_filenames:
                        related.append(f"{base}{h_ext}")
            elif ext in ['.h', '.hpp', '.cuh']:
                for s_ext in ['.cpp', '.cc', '.c', '.cu']:
                    if f"{base}{s_ext}" in all_filenames:
                        related.append(f"{base}{s_ext}")

            f.write(f"## File: [{fname}]({fname})\n")
            if related:
                f.write(f"- **Related**: {', '.join([f'[{r}]({r})' for r in related])}\n")
            
            if not ctx['symbols']:
                f.write("*No public symbols found.*\n")
            for s in ctx["symbols"]:
                f.write(f"### `{s['signature']}`\n")
                f.write(f"- **Type**: {s['type']}\n")
                f.write(f"- **Breadcrumb**: {s['breadcrumb']}\n")
                
                if s.get("bases"):
                    f.write(f"- **Inherits**: {', '.join([f'`{b}`' for b in s['bases']])}\n")
                
                if s.get("fields"):
                    f.write(f"- **Fields**: {', '.join([f'`{fi}`' for fi in s['fields'][:10]])}\n")

                if s.get("calls"):
                    f.write(f"- **Uses**: {', '.join([f'`{c}`' for c in s['calls']])}\n")

                if s.get("summary"):
                    f.write(f"- **Summary**: {s['summary']}\n")
                f.write("\n")
            f.write("---\n")
