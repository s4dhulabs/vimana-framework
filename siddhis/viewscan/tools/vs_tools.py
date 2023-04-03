import re
import ast
import json
import yaml
import os.path
import inspect
import hashlib
import textwrap
from time import sleep
from pygments import highlight
from neotermcolor import cprint,colored as cl
from pygments.lexers import Python3Lexer
from pkg_resources import resource_filename
from pygments.formatters import TerminalFormatter



class handle_sast_output:
    def __init__(self, findings:dict):
        self.findings = findings
        self.rule = findings['rule']

        if self.findings.get('view_path',False):
            app_dir = self.findings['view_path'].split('/')[-2].strip()
            self.scan_dir = f"{self.findings['scan_cache_dir']}/{app_dir}"
        
    def consolidate_sarif_output(self, sarif_files_path:str, output_file:str):
        file_list = get_sarif_files(sarif_files_path)
        results = []

        for file in file_list:
            object = '.'.join(file.split('_vs')[-2].split('/')[-2:])
            rule_signature = file.split('_vs')[-1].split('.')[0]

            status = (f'➣ Consolidating scan results:{cl(object,"green")}:{rule_signature}...')
            print(status.ljust(os.get_terminal_size().columns - 1), end="\r")
            sleep(0.10)

            with open(file, "r") as f:
                output = json.load(f)
                results.extend(output["runs"][0]["results"])
       
        sarif_output = self.get_schema()
        sarif_output["runs"][0]["results"].append(results)  
        

        with open(output_file, "w") as f:
            json.dump(sarif_output, f, indent=4)
        
        if self.findings['output_file']:
            output_file = self.findings['output_file'].replace('.sarif','')
            with open(f"{output_file.strip()}.sarif", "w") as f:
                json.dump(sarif_output, f, indent=4)

        return True

    def get_schema(self):
        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "ViewScan",
                        "version": "1.0",
                        "semanticVersion": "1.0.0",
                        "dottedQuadFileVersion": "1.0.0.0",
                        "fullName": "Vimana Framework Viewscan Plugin",
                        "organization": "s4dhulabs",
                        "shortDescription": {
                            "text": "Simple static analysis utility for Django views"
                        },
                        "description": {
                            "text":"""ViewScan is a tool for identifying potential security issues in Django views. It analyzes the view functions in Django applications and checks for common issues\
                                related to authentication, authorization, and sensitive\
                                data filtering."""
                        },
                        "language": "en-US",
                    }
                },
                "results": []
            }]
        }

    def gen_sarif(self):

        result = {
            "ruleId": self.rule['name'].strip(),
            "level": self.rule['level'],
            "message": {
                "text": self.rule['alert'].strip()
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": self.findings['view_path']
                        },
                        "region": {
                            "startLine": self.findings['start'],
                            "endLine": self.findings['end'],
                        },
                        "contextRegion": {
                            "snippet": {
                                "text": textwrap.dedent(self.findings['node_source']),
                            }
                        }

                    }
                }
            ],
            "fingerprints": [
                {
                    "algorithm": self.findings['algorithm'],
                    "value": self.findings['view_hash']
                }
            ],
        }

        sarif_output = self.get_schema()
        sarif_output["runs"][0]["results"].append(result)

        object_name = self.findings['obj_name'].strip()
        rule_signature = self.rule['signature'][:10]
        object_signature = f"{object_name}_vs{rule_signature}.sarif"
        output_path_file = f"{self.scan_dir}/{object_signature}"
        
        if not os.path.exists(self.scan_dir):
            os.makedirs(self.scan_dir)
            
        if not os.path.exists(output_path_file):
            with open(output_path_file, "w") as f:
                json.dump(sarif_output, f, indent=4)

def to_yaml(node):
    '''
    * rEngine2:
    - yaml_data = to_yaml(node)
    - yaml_data =(yaml.dump(yaml_data))

    '''
    if isinstance(node, ast.AST):
        fields = {}
        for field, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                fields[field] = to_yaml(value)
            elif isinstance(value, list):
                fields[field] = []
                for item in value:
                    if isinstance(item, ast.AST):
                        fields[field].append(to_yaml(item))
                    else:
                        fields[field].append(item)
            else:
                fields[field] = value
        return {type(node).__name__: fields}
    else:
        return str(node)

def find_requirements_file(path):
    for dirpath, dirnames, filenames in os.walk(path):
        if 'requirements.txt' in filenames:
            return os.path.join(dirpath, 'requirements.txt')
    return None

def get_django_version(project_dir:str):
    requirements_file = find_requirements_file(project_dir)
    django_version = False
    reqs=[]

    if requirements_file:
        with open(requirements_file, 'r') as f:
            reqs = f.readlines()

            for req in reqs:
                if 'Django' in req:
                    django_version = req.strip().split('==')[1]
                    break

    return django_version,len(reqs)
        
def get_mod_hash(content):
    return (hashlib.sha256(content.encode('utf-8')).hexdigest())

def hashdir(directory):
    sha256 = hashlib.sha256()

    for root, dirs, files in os.walk(directory):
        sha256.update(root.encode())

        for file in files:
            filepath = os.path.join(root, file)

            with open(filepath, "rb") as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    sha256.update(data)

            sha256.update(filepath.encode())

        for dir in dirs:
            dirpath = os.path.join(root, dir)
            sha256.update(dirpath.encode())

    return sha256.hexdigest()


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

def get_sarif_files(project_dir:str=False):
    pattern = r"_vs[0-9a-f]{10}.sarif$"
    sarif_files = []
    for dirpath, dirnames, filenames in os.walk(project_dir):
        for filename in filenames:
            if re.search(pattern, filename):
                sarif_files.append(os.path.join(dirpath, filename))
    return sarif_files

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


def docrule(issues:list=False):
    frame = inspect.currentframe().f_back
    code = frame.f_code
    rule_name = code.co_name
    rule_signature = get_mod_hash(rule_name)
    engine = frame.f_locals.get('self', None).__class__.__name__
    module_dir = os.path.dirname(os.path.abspath(__file__))
    #yaml_path = os.path.join(module_dir, '..', 'engines',f'{engine}.yaml')
    yaml_path = os.path.join(module_dir, '..', 'engines/rule_docs',f'{engine}.yaml')

    with open(yaml_path) as f:
        rule_file = yaml.safe_load(f)
        rules = rule_file['vs_rules']
        vs_rule = rules[rule_name]
        rule_description = vs_rule['description'].split('\n')
        rule_references = vs_rule['references']

        print(f"    {cl(vs_rule['alert'], 'red',attrs=['bold'])}")
        print()

        for line in rule_description:
            print(f"      {cl(line.strip(),'cyan')}")

        if issues:
            for issue in issues:
                print(f'      * {cl(issue,"red")}')
            print()
        
        cprint(f"    References:", 'white')
        print()
        if rule_references['links']:
            for link in rule_references['links']:
                print(f"      + {cl(link,'cyan')}")
            print()

        if rule_references['cwes']:
            for cwe,cwe_title in rule_references['cwes'].items():
                print(f"      + {cl(cwe,'green')}: {cwe_title}")
        print()

    vs_rule.update(
        {
            'name': rule_name,
            'signature':rule_signature
        }
    )

    return vs_rule

def docme(issues:list=False):
    doc = []
    frame = inspect.currentframe()
    frame = frame.f_back
    code = frame.f_code
    method_name = code.co_name
    constants = code.co_consts

    if constants and isinstance(constants[0], str):
        raw_docs = constants[0].split('\n')
        #docs = constants[0].split('\n')
        alert = raw_docs[1].strip()
        docs = raw_docs[2:]
        print(f"    {cl(alert, 'red')}")

        for line in docs:
            print(f"    {cl(line.strip(),'cyan')}")
        if issues:
            for issue in issues:
                print(f'     + {issue}')
            print()
        print('-' * 100)

    return raw_docs,method_name

def is_validate_password_call_without_password(node:ast.AST=False) -> bool:
    return (isinstance(node, ast.Call) and
        (
            (isinstance(node.func, ast.Attribute) and
            node.func.attr == 'validate_password' and
            node.func.value.id == 'password_validation' and
            'password' not in node.keywords) or
            (isinstance(node.func, ast.Name) and
            node.func.id == 'validate_password' and
            'password' not in node.keywords)
            )
        )
    
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

def check_db_connection(statement):
    is_properly_set_up = True
    issues = []
    for s in statement.body:
        if isinstance(s, ast.Expr):
            if isinstance(s.value, ast.Call):
                if isinstance(s.value.func, ast.Name):
                    # check that the password is not stored in plaintext
                    if s.value.func.id in ["connect", "create_engine"]:
                        for arg in s.value.args:
                            if isinstance(arg, ast.Str):
                                if "password" in arg.s.lower():
                                    is_properly_set_up = False
                                    issues.append("Password found in plaintext in the connection string")
                    # check that the connection is properly closed
                    elif s.value.func.id == "close":
                        pass
                    else:
                        is_properly_set_up = False
                        issues.append(f"Unrecognized function call: {s.value.func.id}")
                elif isinstance(s.value.func, ast.attribute):
                    # check that the password is not stored in plaintext
                    if s.value.func.attr in ["connect", "create_engine"]:
                        for arg in s.value.args:
                            if isinstance(arg, ast.Str):
                                if "password" in arg.s.lower():
                                    is_properly_set_up = False
                                    issues.append("Password found in plaintext in the connection string")
                    # check that the connection is properly closed
                    elif s.value.func.attr == "close":
                        pass
                    else:
                        is_properly_set_up = False
                        issues.append(f"Unrecognized function call: {s.value.func.attr}")

    return (is_properly_set_up, issues)

def check_ssl_setup(if_check):
    is_properly_set_up = True
    issues = []
    for s in if_check.body:
        if isinstance(s, ast.Expr):
            if isinstance(s.value, ast.Call):
                if isinstance(s.value.func, ast.Name):
                    # check that the ssl context is properly set
                    if s.value.func.id in ["create_ssl_context", "create_tls_context"]:
                        pass
                    # check that ssl certificate is properly verified
                    elif s.value.func.id in ["verify_mode", "verify_cert"]:
                        pass
                    # check that the hostname is properly matched with the certificate 
                    elif s.value.func.id == "match_hostname":
                        pass
                    # check that the private key file is present
                    elif s.value.func.id == "load_privatekey":
                        if not os.path.isfile(s.value.args[0].s):
                            is_properly_set_up = False
                            issues.append(f"Invalid private key file path: {s.value.args[0].s}")
                    # check that the certificate file is present
                    elif s.value.func.id == "load_cert_chain":
                        if not os.path.isfile(s.value.args[0].s):
                            is_properly_set_up = False
                            issues.append(f"Invalid certificate file path: {s.value.args[0].s}")
                    # check that the CA file is present
                    elif s.value.func.id == "load_verify_locations":
                        if not os.path.isfile(s.value.args[0].s):
                            is_properly_set_up = False
                            issues.append(f"Invalid CA file path: {s.value.args[0].s}")
                    # check that the protocol is set properly
                    elif s.value.func.id == "PROTOCOL_TLSv1_2":
                        pass
                    else:
                        is_properly_set_up = False
                        issues.append(f"Unrecognized function call: {s.value.func.id}")
                elif isinstance(s.value.func, ast.attribute):
                    # check that the ssl context is properly set
                    if s.value.func.attr in ["create_ssl_context", "create_tls_context"]:
                        pass
                    # check that ssl certificate is properly verified
                    elif s.value.func.attr in ["verify_mode", "verify_cert"]:
                        pass
                    # check that the hostname is properly matched with the certificate 
                    elif s.value.func.attr == "match_hostname":
                        pass
                    # check that the private key file is present
                    elif s.value.func.attr == "load_privatekey":
                        if not os.path.isfile(s.value.args[0].s):
                            is_properly_set_up = False
                            issues.append(f"Invalid private key file path: {s.value.args[0].s}")
                    # check that the certificate file is present
                    elif s.value.func.attr == "load_cert_chain":
                        if not os.path.isfile(s.value.args[0].s):
                            is_properly_set_up = False
                            issues.append(f"Invalid certificate file path: {s.value.args[0].s}")
                    # check that the CA file is present
                    elif s.value.func.attr == "load_verify_locations":
                        if not os.path.isfile(s.value.args[0].s):
                            is_properly_set_up = False
                            issues.append(f"Invalid CA file path: {s.value.args[0].s}")
                    # check that the protocol is set properly
                    elif s.value.func.attr == "PROTOCOL_TLSv1_2":
                        pass
                    else:
                        is_properly_set_up = False
                        issues.append(f"Unrecogniggzed function call: {s.value.func.attr}")
    return (is_properly_set_up, issues)

