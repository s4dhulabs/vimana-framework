import os
import re
import ast
import inspect
from time import sleep
from pygments import lexers
from pygments import highlight
from neotermcolor import colored as cl
from pygments.lexers import Python3Lexer
from urllib.parse import urlparse, urljoin
from pygments.formatters import TerminalFormatter

from ..tools.vs_tools import (
        map_dec_args,
        get_parsed_code_block,
        extract_from_module,
        extract_decorators,
        get_node_decorators
    )


def parse_view(module_path:str) -> dict:
    try:
        with open(module_path) as file:
            module_content = file.read()
            tree = ast.parse(module_content)
    except FileNotFoundError:
        return False

    d = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, 
                (ast.FunctionDef,ast.ClassDef, ast.Lambda)
            ):
            obj_name = node.name
            lineno = node.lineno
            endline = node.end_lineno
            node_source = ast.unparse(node)
            str_node_source = node_source
            raw_decorators = extract_decorators(node_source)
            module_code_block = raw_decorators[:]
            parsed_code_block = []
            firstl = str_node_source.split('\n')[0]
            lastl = str_node_source.split('\n')[-1]
            node_decorators = get_node_decorators(node)
            decargs = map_dec_args(raw_decorators)
            
            module_code_block.extend(
                extract_from_module(module_content,lineno,endline)
            )
            parsed_code_block = get_parsed_code_block(
                module_code_block,lineno
            )
                
            d[obj_name] = {
                'node': node,
                'obj_name': obj_name,
                'hl_code': parsed_code_block,
                'raw_decorators': raw_decorators,
                'dec_args': decargs,
                'node_decorators': node_decorators,
                'view_path': module_path,
                'module_code': module_code_block,
                'node_source': node_source,
                'obj_line': firstl,
                'start': lineno,
                'end': endline
            }
            
            maxp=30
            obj_loc = f"{lineno}-{endline}"
            name = ' '*(maxp - len(obj_name))
            loc =  ' '*(10 - len(obj_loc))
            obj_id = f"{obj_loc + loc} {firstl}"
            obj_spot = (highlight(obj_id,Python3Lexer(),TerminalFormatter()))

            print(f"    {obj_name + name} → {obj_spot.strip()}")

    return d


