import re
import ast
import os.path
import inspect
from pygments import highlight
from neotermcolor import colored as cl
from pygments.lexers import Python3Lexer
from pygments.formatters import TerminalFormatter



def map_dec_args(raw_decorators:list) -> dict:
    pattern = r"\s*@(?P<name>\w+)\((?P<args>.+)\)"
    decargs = {}

    for rdec in raw_decorators:
        args = []
        match = re.match(pattern, rdec)
        if match:
            name = match.group('name')
            args = [arg.replace("'",'').strip() for arg in match.group('args').split(',')]
            decargs[name] = args
        else:
            pass
    return decargs

def get_parsed_code_block(code_block:str, s:int) -> list:
    parsed_code_block = []
    for lno,line in enumerate(code_block, s):
        hline = (f"    {lno}   " + highlight(
            line,Python3Lexer(),TerminalFormatter())
        )
        parsed_code_block.append(hline)
    return parsed_code_block

def extract_from_module(content:str, s:int, e:int) -> str:
    return(content.splitlines()[s-1:e])

def extract_decorators(code:str) -> list:
    decorator_pattern = r'@\w+(?:\(.*\))?'
    return re.findall(decorator_pattern, code)

def get_node_decorators(node:(ast.FunctionDef,ast.ClassDef)) -> list:
    dec_list = []

    if not hasattr(node, 'decorator_list'):
        return dec_list

    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            func_name = dec.func
            if isinstance(func_name, ast.Name):
                decorator = func_name.id
        else:
            decorator = dec.id
        dec_list.append(decorator)

    if hasattr(node, 'body'):
        for item in node.body:
            dec_list.extend(get_node_decorators(item))
    return dec_list


def get_views(project_dir:str=False):
    return [os.path.join(dirpath, filename)
            for dirpath, dirnames, filenames in os.walk(project_dir)
        for filename in filenames if filename == 'views.py'
    ]

def get_patterns_list(urlpatterns: str) -> list:
    patterns=[]

    for match in re.finditer(r"^\s*path\(.*\)",
        urlpatterns, re.MULTILINE
        ):
        patterns.append(match.group(0))
    return patterns

def docme(issues:list=False):
    doc = []
    frame = inspect.currentframe()
    frame = frame.f_back
    code = frame.f_code
    method_name = code.co_name
    constants = code.co_consts

    if constants and isinstance(constants[0], str):
        docs = constants[0].split('\n')
        alert = docs[1].strip()
        docs = docs[2:]
        print(f"    {cl(alert, 'red')}")
        for line in docs:
            print(f"    {cl(line.strip(),'cyan')}")
        if issues:
            for issue in issues:
                print(f'     + {issue}')
            print()
        print('-' * 100)
    return doc

class KeywordVisitor(ast.NodeVisitor):
    def __init__(self, sensitive_params):
        self.sensitive_params = sensitive_params
        self.keywords = set()

    def visit_Attribute(self, node):
        if node.attr in self.sensitive_params:
            self.keywords.add(node.attr)

def check_match(pattern:str, dec_args:dict, check_keys:bool=True) -> bool:
    return any(pattern in dec if check_keys else pattern in args for dec,args in dec_args.items())

class inspect_decorator:
    tracker = set()

    @classmethod
    def run(cls, node_object:str, decorator_type:str, decorators:dict, variables:list):
        findings = []
        if not(check_match(decorator_type, decorators)):
            _issue_ = f"{cl('@' + decorator_type, 'red')} decorator not implemented."
            if _issue_ not in cls.tracker:
                cls.tracker.add(_issue_)
                findings.append(_issue_)
        else:
            for var in variables:
                _issue_ = f"{cl('@' + decorator_type, 'red')} decorator missing potential sensitive parameter: {cl(var, 'red')}"
                if _issue_ not in cls.tracker:
                    if not(check_match(var, decorators, False)):
                            cls.tracker.add(_issue_)
                            findings.append(_issue_)
        return findings

def extract_post_params(node):
    post_params = []
    for child_node in node.body:
        if isinstance(child_node, ast.Expr) and isinstance(child_node.value, ast.Call):
            for keyword in child_node.value.keywords:
                if isinstance(keyword.value, ast.Subscript) and isinstance(keyword.value.slice, ast.Constant):
                    post_params.append(keyword.value.slice.value)
    return post_params

def is_POST_request(keyword):
    try:
        return all([isinstance(keyword.value, ast.Subscript),
            isinstance(keyword.value.value, ast.Attribute),
            keyword.value.value.attr == 'POST',
            isinstance(keyword.value.value.value, ast.Name),
            keyword.value.value.value.id == 'request'
        ])
    except AttributeError:
        return False


