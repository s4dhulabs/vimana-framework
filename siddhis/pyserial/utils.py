# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
#
# This file is part of Vimana Framework Project.

from core._dbops_.vmnf_dbops import VFDBOps

from pygments.formatters import TerminalFormatter
from neotermcolor import colored, cprint
from pygments.lexers import JsonLexer,BrainfuckLexer,TextLexer
from pygments import highlight
import hashlib
from time import sleep
import logging
import os
import json

from prettytable import PrettyTable


method_colors = {
    "GET": 28,        
    "POST": 32,       
    "PUT": 226,       
    "DELETE": 196,    
    "PATCH": 214,     
    "OPTIONS": 88,    
    "HEAD": 240
}


spec_dir = '~/vimana/__cache__/fastapi/specs/'

def jcbanner():
    print(
        f"""

            _
         -='-ø'`
              \ \\
               ø {colored('JCølt',99)}
              .ø |.---,
              :ø ||  |
               \ ~   |
                '._.'
                {colored('VimanaFramework v1.0', 8)}
                        @s4dhulabs

        """
    )

def jcbanner_fmt(spec_info_dict):
    print('\033[2J\033[1;1H' * 3)
    banner_lines = [
        "            _",
        "         -='-ø'`",
        "              \\ \\",
        f"               ø JCølt",
        "              .ø |.---,",
        "              :ø ||  |",
        "               \\ ~   |",
        "                '._.'",
    ]

    ignore_keys = ['id', '_sa_instance_state', 'spec_file_path']
    spec_info_lines = [f"{colored(k,95):>30}: {colored(v,99)}" for k, v in spec_info_dict.items() if k not in ignore_keys]
    max_lines = max(len(banner_lines), len(spec_info_lines))

    while len(banner_lines) < max_lines:
        banner_lines.append("")

    while len(spec_info_lines) < max_lines:
        spec_info_lines.append("")

    for banner_line, spec_info_line in zip(banner_lines, spec_info_lines):
        print(f"{banner_line:<30} {spec_info_line}")
    print()

from neotermcolor import colored, cprint

def sort_list(items:list) -> list:
        return sorted(items, key=lambda i: len(i), reverse=True)

def get_specs():
    return (VFDBOps().list_resource('_SPECS_',[]))
    
def get_methods(data):
    m_list = []
    for p, ms in data.get('paths').items():
        for m, p in ms.items():
            m_list.append(m.upper())           

    return ','.join(list(set(m_list)))       

  

def flush_specs(spec_ids=None, remove_all=False): 
    #$ vimana run --plugin jcolt --flush-specs 
    if remove_all:
        specs = VFDBOps().list_resource('_SPECS_', [])
        if not specs:
            print(' → jcolt@utils: No spec found!')
            print()
            return False
    
        for spec in specs:
            print(
                f" → Removing spec {spec.spec_id} - {spec.spec_title}: {spec.spec_host} ({spec.spec_methods})..."
            )
            sleep(0.01)
            
            VFDBOps().flush_resource('_SPECS_', 'spec_id', spec.spec_id)

            try:    
                os.remove(spec.spec_file_path)
            except FileNotFoundError as e:
                logging.error(f"Error removing specfile {spec.spec_id}: {e}")
                print()
        print()
    else:
        #$ vimana run --plugin jcolt --flush-spec aSb988
        for s_id in spec_ids:
            spec = VFDBOps().get_by_id('_SPECS_', 'spec_id', s_id)

            if not spec:
                print(f" => Spec {s_id} not found!")
                print()
                continue
            
            if os.path.exists(spec.spec_file_path):
                os.remove(spec.spec_file_path)
                VFDBOps(**{}).flush_resource('_SPECS_','spec_id',s_id)
                print(
                    f" → Removing spec {spec.spec_id} - {spec.spec_title}: {spec.spec_host} ({spec.spec_methods})..."
                )
                sleep(1)
                print()
            else:
                print(f" → Spec file {s_id} not found!")
                print()
def list_specs():
    specs = get_specs()

    if not specs:
        print(' → jcolt@utils: No spec found')
        print()
        return False
    
    output_table = PrettyTable()
    output_table.title = f"jc0lt - {len(specs)} specs"
    output_table.field_names = ["Index", "ID", "Title", "FastAPI", "OpenAPI", "Host", "Paths", "Methods", "Date"]
    output_table.align = 'l'

    for tbl_index,spec in enumerate(specs,1):
        output_table.add_row(
            [
                tbl_index,
                colored(spec.spec_id,49), 
                spec.spec_title[:20], 
                spec.fastapi_version,
                spec.openapi_version,
                spec.spec_host, 
                spec.spec_paths, 
                spec.spec_methods,
                spec.spec_date
            ]
        )

    print(output_table)
    print()
    return specs

def gen_path_id(_method_:str, api_endpoint:str) -> str:
    #input(f"{_method_}:{api_endpoint}")
    return _method_[0] + get_hash(f"{_method_}:{api_endpoint}")[:4]

def get_hash(content):
    return (hashlib.sha256(content.encode('utf-8')).hexdigest())

def parse_schema_references(data:dict) -> list:
    ref_values = []

    def extract_refs(obj):
        if isinstance(obj, dict):
            if '$ref' in obj:
                ref_values.append(obj['$ref'])
            for value in obj.values():
                extract_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_refs(item)

    extract_refs(data)
    return ref_values

def parse_schema_reference(request_body:dict) -> str:
    ref_value = False
    for content_type, content_data in request_body['content'].items():
        if 'schema' in content_data:
            ref_value = content_data['schema'].get('$ref',False)

    return ref_value

def get_schema_parameters(api_specs:dict, ref_path:str) -> dict:
    ref_parts = ref_path.split('/')
    current = api_specs

    for part in ref_parts:
        if part == '#':
            continue
        current = current[part]

    return current

def align_json(json_dump:str, align_number:int=17, color_def:int=None) -> str:
    aligned_json_lines = json_dump.split('\n')
    
    if color_def:
        aligned_json_lines = [f"{' ' * align_number}{colored(line,color_def)}" for line in aligned_json_lines]
    else:
        aligned_json_lines = [f"{' ' * align_number}{line}" for line in aligned_json_lines]

    return '\n'.join(aligned_json_lines)

def parse_requestBody(
    api_specs:dict, 
    requestBody:dict, 
    lexer_disabled:bool=False,
    disable_output:bool=False
    ) -> str:

    ref_paths = parse_schema_references(requestBody)
    setLexer = JsonLexer()
    json_dump = ''

    if lexer_disabled:
        setLexer = TextLexer()
    
    if ref_paths:
        for ref_path in ref_paths:
            params = get_schema_parameters(api_specs, ref_path)
            json_dump = json.dumps(params, indent=4)
            aligned_json_aligned = align_json(json_dump,12)
            highlighted_json = highlight(aligned_json_aligned, setLexer, TerminalFormatter())

            if not disable_output:
                print(highlighted_json)
    
    return json_dump

def export_body(json_dump: str, spec_id: str) -> str:
    if not json_dump:
        return ""

    title = json_dump.get('title', "")
    required_args = json_dump.get('required', [])
    properties = json_dump.get('properties', {})

    body_reqs_all = {key: val['type'] for key, val in properties.items()}
    body_reqs = {key: val for key, val in body_reqs_all.items() if key in required_args}

    export_relpath = f'{spec_id}_exports/{title}'
    full_export_path = os.path.join(os.getcwd(), export_relpath)
    os.makedirs(full_export_path, exist_ok=True)

    with open(f"{full_export_path}/all_properties.json", 'w+') as f:
        json.dump(body_reqs_all, f, indent=4)

    with open(f"{full_export_path}/required_properties.json", 'w+') as f:
        json.dump(body_reqs, f, indent=4)

    print(f"  ➤  Request Body exported to {colored(export_relpath, 'red')}\n\n")
    
    return full_export_path

def get_query_string(body:dict):
    query_string = ""
    for key, value in body['properties'].items():
        is_required = key in body.get('required', [])
        flag = "$JCF-P" if not is_required else "$JCF-R"
        query_string += f"{key}={flag}&"

    return query_string.rstrip('&')

def get_parameters(path, parameter_list):
    path_with_parameters = path

    for param in parameter_list:
        name = param['name']
        required = param.get('required', False)
        flag = "$JCF-R" if required else "$JCF-P"

        if '?' in path_with_parameters:
            path_with_parameters += f"&{name}={flag}"
        else:
            path_with_parameters += f"?{name}={flag}"

    return path_with_parameters

