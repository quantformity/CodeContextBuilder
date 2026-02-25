import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv
import pathlib

# Load from .ccbenv instead of .env
env_path = pathlib.Path(".ccbenv")
load_dotenv(dotenv_path=env_path)

@dataclass
class LLMConfig:
    provider: str = os.getenv("LLM_PROVIDER", "ollama")
    model: str = os.getenv("LLM_MODEL", "llama3")
    base_url: Optional[str] = os.getenv("LLM_BASE_URL")
    api_key: Optional[str] = os.getenv("LLM_API_KEY")

@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    include: List[str] = field(default_factory=lambda: os.getenv("INCLUDE_PATTERNS", "**/*.ts,**/*.py,**/*.go,**/*.java,**/*.c,**/*.h,**/*.cpp,**/*.hpp,**/*.cu,**/*.cuh").split(","))
    exclude: List[str] = field(default_factory=lambda: os.getenv("EXCLUDE_PATTERNS", "**/node_modules/**,**/dist/**,**/build/**,**/.git/**").split(","))
    output_file_name: str = os.getenv("OUTPUT_FILE_NAME", ".context.md")

config = AppConfig()
