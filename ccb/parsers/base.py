from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from tree_sitter import Node

@dataclass
class SymbolInfo:
    name: str
    type: str 
    signature: str
    breadcrumb: str
    line_start: int
    line_end: int
    is_public: bool
    code: str
    summary: Optional[str] = None
    bases: List[str] = None
    fields: List[str] = None
    calls: List[str] = None # List of functions/methods called by this symbol

    def to_dict(self):
        return asdict(self)

class BaseParser:
    def supports(self, extension: str) -> bool:
        raise NotImplementedError()

    def parse(self, code: str, file_path: str) -> List[SymbolInfo]:
        raise NotImplementedError()

    def get_signature(self, node: Node) -> str:
        text = node.text.decode('utf-8') if isinstance(node.text, bytes) else node.text
        return text.split('\n')[0].strip()
    
    def get_node_text(self, node: Node) -> str:
        return node.text.decode('utf-8') if isinstance(node.text, bytes) else node.text
