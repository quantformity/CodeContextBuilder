import tree_sitter_languages
import tree_sitter
from tree_sitter import Node
from .base import BaseParser, SymbolInfo
from typing import List, Optional

class UniversalParser(BaseParser):
    def __init__(self, lang_id: str, extensions: List[str]):
        self.lang_id = lang_id
        self.extensions = extensions
        self.language = tree_sitter_languages.get_language(lang_id)
        self.parser = tree_sitter.Parser()
        self.parser.set_language(self.language)

    def supports(self, extension: str) -> bool:
        return extension in self.extensions

    def parse(self, code: str, file_path: str) -> List[SymbolInfo]:
        tree = self.parser.parse(bytes(code, "utf8"))
        symbols = []
        self._visit(tree.root_node, "", symbols)
        return symbols

    def _visit(self, node: Node, breadcrumb: str, symbols: List[SymbolInfo]):
        current_breadcrumb = breadcrumb
        
        symbol_type = None
        if node.type in ['class_definition', 'class_specifier', 'struct_specifier', 'interface_declaration']:
            symbol_type = 'class'
        elif node.type in ['function_definition', 'function_declaration', 'method_declaration', 'method_definition']:
            symbol_type = 'method' if breadcrumb else 'function'
        elif node.type == 'declaration' and self.lang_id in ['cpp', 'c']:
            symbol_type = 'function'

        if symbol_type:
            name = self._get_name(node)
            if name and self._is_public(name, node):
                display_name = name
                if "::" in name:
                    parts = name.split("::")
                    display_name = parts[1]
                    class_name = parts[0]
                    current_breadcrumb = f"{breadcrumb} > {class_name}" if breadcrumb else class_name

                if symbol_type == 'class':
                    current_breadcrumb = f"{breadcrumb} > {display_name}" if breadcrumb else display_name
                
                docstring = self._get_docstring(node)
                
                # Metadata
                bases = self._get_bases(node) if symbol_type == 'class' else []
                fields = self._get_fields(node) if symbol_type == 'class' else []
                calls = self._get_calls(node) # Extract calls within this body

                symbols.append(SymbolInfo(
                    name=display_name,
                    type=symbol_type,
                    signature=self.get_signature(node),
                    breadcrumb=f"{current_breadcrumb} > {display_name}" if symbol_type == 'method' and "::" not in name else current_breadcrumb if symbol_type == 'class' else f"{breadcrumb} > {display_name}" if breadcrumb else display_name,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                    is_public=True,
                    code=self.get_node_text(node),
                    summary=docstring,
                    bases=bases,
                    fields=fields,
                    calls=calls
                ))

        for child in node.children:
            self._visit(child, current_breadcrumb, symbols)

    def _get_calls(self, root_node: Node) -> List[str]:
        """Lightweight call extraction using AST."""
        calls = set()
        
        # Mapping of node types that represent a function call in different languages
        call_node_types = ['call', 'call_expression', 'method_invocation']
        
        def find_calls(node: Node):
            if node.type in call_node_types:
                # Extract name from the call node
                # e.g., Python: (call function: (identifier))
                # e.g., Java: (method_invocation name: (identifier))
                name_node = node.child_by_field_name('function') or \
                            node.child_by_field_name('name') or \
                            node.child_by_field_name('declarator')
                
                if not name_node:
                    # Fallback for some grammars where the first child is the function name
                    for child in node.children:
                        if child.type in ['identifier', 'attribute', 'field_expression', 'member_expression']:
                            name_node = child
                            break
                
                if name_node:
                    call_name = name_node.text.decode('utf8') if isinstance(name_node.text, bytes) else str(name_node.text)
                    # Clean class member calls (e.g., self.login -> login)
                    if "." in call_name: call_name = call_name.split(".")[-1]
                    if "->" in call_name: call_name = call_name.split("->")[-1]
                    if "::" in call_name: call_name = call_name.split("::")[-1]
                    calls.add(call_name)

            for child in node.children:
                find_calls(child)

        find_calls(root_node)
        return list(calls)

    def _get_bases(self, node: Node) -> List[str]:
        bases = []
        if self.lang_id == 'python':
            args = node.child_by_field_name('superclasses')
            if args: bases = [c.text.decode('utf8') for c in args.children if c.type == 'identifier']
        elif self.lang_id == 'java':
            for child in node.children:
                if child.type in ['superclass', 'interfaces']:
                    bases.extend([c.text.decode('utf8') for c in child.children if c.type in ['type_list', 'type_identifier']])
        elif self.lang_id == 'cpp':
            base_clause = node.child_by_field_name('base_class_clause')
            if base_clause:
                bases = [c.text.decode('utf8') for c in base_clause.children if c.type == 'type_identifier']
        return bases

    def _get_fields(self, node: Node) -> List[str]:
        fields = []
        body = node.child_by_field_name('body')
        if body:
            for child in body.children:
                if child.type in ['field_declaration', 'variable_declaration']:
                    name = self._get_name(child)
                    if name: fields.append(name)
        return fields

    def _get_name(self, node: Node) -> str:
        name_node = node.child_by_field_name('name')
        if not name_node:
            declarator = node.child_by_field_name('declarator')
            while declarator and declarator.child_by_field_name('declarator'):
                declarator = declarator.child_by_field_name('declarator')
            
            if declarator:
                for child in declarator.children:
                    if child.type in ['identifier', 'field_identifier', 'qualified_identifier']:
                        return child.text.decode('utf8') if isinstance(child.text, bytes) else str(child.text)

            for child in node.children:
                if child.type in ['identifier', 'field_identifier']: 
                    text = child.text
                    return text.decode('utf8') if isinstance(text, bytes) else str(text)
        if name_node:
            text = name_node.text
            return text.decode('utf8') if isinstance(text, bytes) else str(text)
        return ""

    def _get_docstring(self, node: Node) -> Optional[str]:
        if self.lang_id == 'python':
            body = node.child_by_field_name('body')
            if body and body.children:
                first_stmt = body.children[0]
                if first_stmt.type == 'expression_statement':
                    string_node = first_stmt.children[0]
                    if string_node.type == 'string':
                        return string_node.text.decode('utf8').strip('"' + "'")

        comments = []
        curr = node.prev_sibling
        while curr and curr.type in ['comment', 'line_comment', 'block_comment']:
            text = curr.text.decode('utf8').strip()
            text = text.lstrip('/#* ').rstrip('/#* ')
            if text:
                comments.insert(0, text)
            curr = curr.prev_sibling
        
        return " ".join(comments) if comments else None

    def _is_public(self, name: str, node: Node) -> bool:
        if self.lang_id == 'python':
            return not name.startswith('_') or name.startswith('__')
        if self.lang_id == 'go':
            return name[0].isupper() if name else False
        if self.lang_id == 'java':
            text = node.text
            text_str = text.decode('utf8') if isinstance(text, bytes) else str(text)
            return 'public' in text_str.split('{')[0]
        if self.lang_id in ['cpp', 'c']:
            text = node.text
            text_str = text.decode('utf8') if isinstance(text, bytes) else str(text)
            return 'static' not in text_str.split('{')[0]
        return True
