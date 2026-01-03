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
import os
import re
import sys
import json
import copy
import string
import random
from neotermcolor import colored
from ..utils import align_json, parse_requestBody
#           from ..jamfuzz import navifuzz
from ..navi.handler import navi_handler

from ..engines.fetcher import jcfetcher

import uuid
from datetime import datetime, timedelta
from mimesis import Generic

class Jcfzz:
    def __init__(self, vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.set_path_scope = self.vmnf_handler.get('set_path_scope', False)
        self.set_param_scope = self.vmnf_handler.get('set_param_scope', False)
        if self.set_param_scope:
            self.set_param_scope = [p.strip() for p in self.set_param_scope.split(',')]

        self.use_custom_variations = self.vmnf_handler.get('fuzzer_custom_variations', False)
        self.spec_id = self.vmnf_handler['spec_id']
        self.schema = self.vmnf_handler['schema'] 
        self.fuzz_scope = self.vmnf_handler.pop('fuzz_scope')
                                                
        self.genData = Generic('en')

    def get_request_body_schema(self, api_specs, path):
        # Usar parse_requestBody para extrair o esquema do corpo da requisição
        requestBody = api_specs.get('paths', {}).get(path, {}).get('post', {}).get('requestBody', {})
        json_dump = parse_requestBody(api_specs, requestBody, lexer_disabled=True, disable_output=True)
        schema = json.loads(json_dump) if json_dump else {}
        return schema

    def generate_value(self, prop_schema):
        prop_type = prop_schema.get('type')
        if prop_type == 'string':
            return self.genData.person.password()
        elif prop_type == 'integer':
            return random.randint(0, 87811)
        elif prop_type == 'array':
            items_schema = prop_schema.get('items', {})
            return [self.generate_value(items_schema)]
        elif prop_type == 'object':
            return self.generate_object(prop_schema)
        return None

    def generate_object(self, schema):
        obj = {}
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        for prop, prop_schema in properties.items():
            if prop in required:
                obj[prop] = self.generate_value(prop_schema)
        return obj

    def generate_valid_request_body(self, schema):
        return self.generate_object(schema)

    def generate_fuzzed_request_bodies(self, schema):
        num_variations = self.use_custom_variations if self.use_custom_variations else 3
        valid_body = self.generate_valid_request_body(schema)
        fuzzed_bodies = []

        # Adicionar um corpo vazio
        fuzzed_bodies.append({})

        # Adicionar o corpo válido
        fuzzed_bodies.append(valid_body)

        for _ in range(num_variations):
            fuzzed_body = valid_body.copy()
            self.fuzz_schema(fuzzed_body, schema)
            fuzzed_bodies.append(fuzzed_body)

        return fuzzed_bodies

    def randnotes(self):
        return [
            ''.join(random.choices(string.ascii_letters, k=10)) + self.genData.person.email().split('@')[1],
            ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
            str(uuid.uuid4()),
            ''.join(random.choices(string.ascii_letters + string.digits, k=36)),
            self.genData.internet.ip_v6().replace(':', '-'),
            self.genData.internet.ip_v6(),
            random.randint(-1000, 1000),
            ''.join(random.choices(string.punctuation, k=10)),
            self.genData.numeric.complex_number(),
            self.genData.text.hex_color(),
            self.genData.code.isbn(),
            self.genData.internet.query_parameters()

        ]
        
    def fuzz_schema(self, body, schema):
        # $ vimana run --plugin jcolt --fuzzspec aSb988 --custom-variations 6
        num_variations = self.use_custom_variations if self.use_custom_variations else 3
        num_variations = min(max(num_variations, 1), 6)  # Ensure num_variations is between 1 and 6

        for prop, prop_schema in schema.get('properties', {}).items():
            prop_type = prop_schema.get('type')
            if prop_type == 'string':
                format = prop_schema.get('format')
                if format == 'email':
                    fuzzed_values = [
                        ''.join(random.choices(string.ascii_letters, k=10)) + self.genData.person.email().split('@')[1],
                        ''.join(random.choices(string.ascii_letters + string.digits, k=256)) + self.genData.person.email().split('@')[1],
                        ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
                        None,
                        False,
                        self.genData.person.email(),
                    ]
                elif format == 'url':
                    fuzzed_values = [
                        'http://' + ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + self.genData.internet.top_level_domain(),
                        'https://' + ''.join(random.choices(string.ascii_letters + string.digits, k=256)) + self.genData.internet.top_level_domain(),
                        ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
                        None,
                        self.genData.internet.top_level_domain(),
                        self.genData.internet.url()
                    ]
                elif format == 'uuid':
                    fuzzed_values = [
                        str(uuid.uuid4()),
                        ''.join(random.choices(string.ascii_letters + string.digits, k=36)),
                        None,
                        self.genData.internet.ip_v6().replace(':', '-'),
                        self.genData.internet.ip_v6(),
                        '00000000-0000-0000-0000-000000000000'
                    ]
                
                else:
                    fuzzed_values = [
                        ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
                        ''.join(random.choices(string.ascii_letters + string.digits, k=256)),
                        ''.join(random.choices(string.punctuation, k=10)),
                        ''.join(random.choices(string.whitespace, k=10)),
                        ''.join(chr(random.randint(0, 31)) for _ in range(10)),
                        None
                    ]

                body[prop] = random.choice(fuzzed_values[:num_variations])
            
            elif prop_type == 'integer':
                fuzzed_values = [
                    random.randint(-1000, 1000),
                    random.randint(1, 2**31-1),
                    -2**31,
                    2**31-1,
                    None,
                    0
                ]
                body[prop] = random.choice(fuzzed_values[:num_variations])
            
            elif prop_type == 'number':
                fuzzed_values = [
                    random.uniform(-1000.0, 1000.0),
                    random.uniform(1.0, 1e10),
                    float('nan'),
                    float('inf'),
                    -float('inf'),
                    None
                ]
                body[prop] = random.choice(fuzzed_values[:num_variations])
            
            elif prop_type == 'boolean':
                fuzzed_values = [
                    random.choice([True, False]),
                    random.choice(['true', 'false']),
                    None,
                    1,
                    0,
                    'yes'
                ]
                body[prop] = random.choice(fuzzed_values[:num_variations])
            
            elif prop_type == 'array':
                fuzzed_values = [
                    [],
                    [random.randint(0, 100) for _ in range(random.randint(1, 100))],
                    [None],
                    [{"unexpected": ''.join(random.choices(string.ascii_letters, k=10))}],
                    [random.choice([True, False, None, '', 0, 1.0])] * 1000,
                    [random.choice([True, False, None, '', 0, 1.0])] * 10
                ]
     
                body[prop] = random.choice(fuzzed_values[:num_variations])
            
            elif prop_type == 'object':
                fuzzed_values = [
                    {},
                    {"unexpected": ''.join(random.choices(string.ascii_letters, k=10))},
                    {"nested": {"unexpected": ''.join(random.choices(string.ascii_letters, k=10))}},
                    {"deeply": {"nested": {"object": {"with": {"many": {"levels": "deep"}}}}}},
                    None,
                    {"simple": "object"}
                ]
                body[prop] = random.choice(fuzzed_values[:num_variations])
            
            elif prop_type == 'date':
                fuzzed_values = [
                    (datetime.now() + timedelta(days=random.randint(-365, 365))).isoformat(),
                    ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
                    None,
                    '2021-01-01T00:00:00Z',
                    'invalid-date',
                    '2021-12-31'
                ]
                body[prop] = random.choice(fuzzed_values[:num_variations])
            
            elif prop_type == 'enum':
                allowed_values = prop_schema.get('enum', [])
                fuzzed_values = allowed_values + [''.join(random.choices(string.ascii_letters, k=10)), None, 'invalid-enum']
                body[prop] = random.choice(fuzzed_values[:num_variations])
                        
            elif prop_schema.get('anyOf'):
                for sub_schema in prop_schema['anyOf']:
                    sub_type = sub_schema.get('type')
                    if sub_type:
                        prop_type = sub_type
                        break

                # Recurse with the sub-schema
                self.fuzz_schema(body, {'properties': {prop: sub_schema}})
            else:
                #print(f"Unsupported property type: {prop_type} -> {prop_schema}")
                pass

            # Randomly remove some properties to simulate missing fields
            if random.choice([True, False]):
                body.pop(prop, None)

    def process_request_body(self, api_specs, path):
        schema = self.get_request_body_schema(api_specs, path)
        fuzzed_bodies = self.generate_fuzzed_request_bodies(schema)
        
        # Remover duplicatas
        unique_bodies = []
        seen_bodies = set()
        
        for body in fuzzed_bodies:
            body_str = json.dumps(body, sort_keys=True)
            if body_str not in seen_bodies:
                seen_bodies.add(body_str)
                unique_bodies.append(body)
        
        # Alinhar e formatar os corpos de requisição
        aligned_fuzzed_bodies = [align_json(json.dumps(body, indent=4), 12) for body in unique_bodies]
  
        return aligned_fuzzed_bodies

    def check_no_specified_status(self, fuzz_case):
        # get the first case from the fuzz results / responses
        case = next(iter(next(iter(fuzz_case.values()))))

        # get the expected status codes from the spec
        expected_responses = case['properties'].get('responses')
        
        # it's also a mistake to not have any expected status codes
        if not expected_responses:
            print(f"  {colored('No expected status codes specified', 99)}")
            return fuzz_case

        # get the status codes from the responses (Specs)
        expected_status_codes = [int(s) for s in expected_responses.keys()]
        
        for path, responses in fuzz_case.items():
            for response in responses:
                response_status = response['response'].status   
                response['response_status_audit'] = {
                    'fuzz_response_status': False,        
                    'expected_status_codes': expected_status_codes,
                    'expected_responses': expected_responses
                }             
                if response_status not in expected_status_codes:
                    response['response_status_audit'].update({
                        'fuzz_response_status': response_status        
                        }
                    )

        return fuzz_case

    def start_fuzzing(self, fuzz_scope):
        fuzz_results = {}

        for path, bodies in fuzz_scope.items():
            request_dict = bodies[0]
            properties = request_dict['properties']
            summary = properties.get('summary')
            tags = ','.join(properties.get('tags','') )
            sum_op = f"{summary}: {tags}"
            ss = ' ' * (100 - len(sum_op))

            print()
            print(f"{colored('  ' + sum_op + ss, 436, 99, attrs=['bold'])}")
            print()

            # fuzz all the variations for the current endpoint body
            fetcher = jcfetcher(bodies, **self.vmnf_handler)
            fetcher.start()
            fuzz_response = fetcher.fuzz_results

            # enrich fuzz results with status checks
            fuzz_response = self.check_no_specified_status(fuzz_response)
            '''
            for i in (fuzz_response[path]):
                if 'response_status_audit' in i:
                    print(i)
                    print('='   * 100)
           # input('done')
           '''
            
            # update fuzz results with the new fuzz object updated with fuzz response details
            fuzz_results.update(fuzz_response)

        # Handle JSON export if requested
        if self.vmnf_handler.get('json_output') or self.vmnf_handler.get('output'):
            self._export_results_to_json(fuzz_results)

        # call the navi handler to manage the results in a visual fashion
        if self.vmnf_handler.get('navigation_mode'):
            navi_handler(self.vmnf_handler).manage(fuzz_results)
        #else:
        #    print(fuzz_results)
        
    def _export_results_to_json(self, fuzz_results):
        """Export fuzz results to JSON format."""
        try:
            from ..exporters.json_exporter import JcoltFuzzspecJsonExporter
            
            # Extract spec info if available
            spec_info = {}
            if hasattr(self, 'spec_id'):
                spec_info['spec_id'] = self.spec_id
            if hasattr(self, 'schema'):
                info = self.schema.get('info', {})
                spec_info.update({
                    'title': info.get('title', 'Unknown API'),
                    'version': info.get('version', 'Unknown'),
                    'description': info.get('description', '')
                })
                
                # Extract host information from servers or first fuzz entry
                host = None
                servers = self.schema.get('servers', [])
                if servers and len(servers) > 0:
                    host = servers[0].get('url', '')
                else:
                    # Fallback: get host from first fuzz entry
                    for path_entries in fuzz_results.values():
                        if path_entries:
                            host = path_entries[0].get('host', '')
                            break
                
                if host:
                    spec_info['host'] = host
            
            # Create exporter instance
            output_file = self.vmnf_handler.get('output')
            exporter = JcoltFuzzspecJsonExporter(output_file=output_file, spec_info=spec_info)
            
            # Additional metadata
            additional_metadata = {
                'test_mode': 'fuzzspec',
                'command_line_args': {
                    'set_path_scope': getattr(self, 'set_path_scope', None),
                    'set_param_scope': getattr(self, 'set_param_scope', None),
                    'navigation_mode': self.vmnf_handler.get('navigation_mode', False)
                }
            }
            
            # Export with summary stats
            export_summary = exporter.export_with_summary_stats(fuzz_results, additional_metadata)
            
            # Display summary if not in quiet mode
            if not self.vmnf_handler.get('quiet', False):
                stats = export_summary['statistics']
                print(f"\n → JSON Export Summary:")
                print(f"   • File: {export_summary['output_file']}")
                print(f"   • Endpoints: {stats['total_endpoints']}")
                print(f"   • Requests: {stats['total_requests']}")
                print(f"   • Error Rate: {stats['error_rate']:.1f}%")
                if spec_info.get('host'):
                    print(f"   • Target Host: {spec_info['host']}")
                
        except ImportError as e:
            print(f" → Error: JSON exporter not available: {e}")
        except Exception as e:
            print(f" → Error exporting to JSON: {e}")

    def generate_fuzzing_variations(self, dictionaries):
        # Tipos de dados para fuzzing
        fuzz_values = {
            'grant_type': ['implicit', 'authorization_code', 'refresh_token', random.uniform(-1000.0, 1000.0),False],
            'username': [self.genData.person.username(), ' ', random.uniform(-1000.0, 1000.0), True],
            'password': [self.genData.person.password(), random.uniform(-1000.0, 1000.0), None],
            'scope': ['read', 'write', 'admin', 'user', 'all', 'root',random.uniform(-1000.0, 1000.0), 'True'],
            'client_id': [self.genData.person.random.generate_string('s3cr3t'), 'cliend_id', random.uniform(-1000.0, 1000.0), ' '],
            'client_secret': [self.genData.person.password(), self.genData.person.password(),random.uniform(-1000.0, 1000.0), ' ']
        }

        new_entries = []

        for dictionary in dictionaries:
            body = dictionary.get('body', '')
            if body:
                params = body.split('&')
                for param in params:
                    key, value = param.split('=')
                    if value == '$JCF-P' or value == '$JCF-R':
                        if key in fuzz_values:
                            for fuzz_value in fuzz_values[key]:
                                new_entry = dictionary.copy()
                                new_body = []
                                for p in params:
                                    k, v = p.split('=')
                                    if k == key:
                                        new_body.append(f"{k}={fuzz_value}")
                                    else:
                                        new_body.append(p)
                                new_entry['body'] = '&'.join(new_body)
                                new_entries.append(new_entry)

        dictionaries.extend(new_entries)
        
    def expand_fuzz_scope(self, filtered_fuzz_scope):
        for path in list(filtered_fuzz_scope.keys()):
            new_entries = []
            for x in filtered_fuzz_scope[path]:
                body = x.get('body', '')
                if 'JCF-R' in body or 'JCF-P' in body:
                    # Split the body into parameters
                    params = body.split('&')
                    
                    # Generate new dictionaries with parameters in order
                    for i in range(1, len(params) + 1):
                        new_body = '&'.join(params[:i])
                        new_entry = x.copy()
                        new_entry['body'] = new_body
                        new_entries.append(new_entry)

            # Add the new entries to the filtered_fuzz_scope
            self.generate_fuzzing_variations(new_entries)
            '''
            for new_entry in new_entries:
                print(new_entry)
                print('-'   * 100)
            #input('jcfzz-332')
            '''
            filtered_fuzz_scope[path].extend(new_entries)

    def generate_payload_paths(self,path):
        match = re.search(r'\{(\w+)\}', path)
        if not match:
            return [path]  

        param_name = match.group(1)
        payloads = self.randnotes()

        new_paths = []
        for payload in payloads:
            new_path = path.replace(f'{{{param_name}}}', str(payload))
            new_paths.append(new_path)

        return new_paths

    def manage(self):
        # filter scope if set_path_scope is set, we use it in other parts of vimana framework too
        filtered_fuzz_scope = {}
        new_payload_paths = None
        
        all_params = set()

        for path in self.fuzz_scope.keys():
            # e.g: $ vimana run --plugin jcolt --fuzzspec aSb988 --set-path /token
            if self.set_path_scope and path != self.set_path_scope:
                continue

            # e.g: $ vimana run --plugin jcolt --fuzzspec aSb988 --set-parameter item_id
            if self.set_param_scope:     
                from time import sleep
                from ..cmd.list import jcList
                self.jc_list = jcList(self.schema)
                parameters = self.jc_list.list_parameters(path)
                current_params = [p['name'] for m in parameters.values() for params in m.values() for p in params]

                if not current_params:
                    continue

                if not any(param in current_params for param in self.set_param_scope):
                    continue
                    
                new_payload_paths = self.generate_payload_paths(path)
                if not new_payload_paths:
                    print(f"  {colored('No payloads generated for path', 99)}")
                    sleep(1)
                    continue
            
            # picks the first entry for the current endpoint as a template to build fuzzing scope
            seed_body = self.fuzz_scope[path][0]   
            # seedbody_schema
            '''
                {
                "properties": {
                    "summary": "Login For Access Token",
                    "operationId": "login_for_access_token_token_post",
                    "requestBody": {
                    "content": {
                        "application/x-www-form-urlencoded": {
                        "schema": {
                            "$ref": "#/components/schemas/Body_login_for_access_token_token_post"
                        }
                        }
                    },
                    "required": true
                    },
                    "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                        "application/json": {
                            "schema": {
                            "$ref": "#/components/schemas/Token"
                            }
                        }
                        }
                    },
                    "422": {
                        "description": "Validation Error",
                        "content": {
                        "application/json": {
                            "schema": {
                            "$ref": "#/components/schemas/HTTPValidationError"
                            }
                        }
                        }
                    }
                    }
                },
                "method": "post",
                "host": "http://127.0.0.1:8000",
                "path": "/token",
                "body": {}
                }
            '''

            # get bodie fuzz variations based on the spec schema for each path
            fuzz_spec_bodies = self.process_request_body(self.schema, path)
            
            # for each fuzz body constructed, update the seed body with the fuzz body
            for body in fuzz_spec_bodies:
                seed_body_copy = copy.deepcopy(seed_body)
                seed_body_copy['body'] = body

                # append the variation to the current endpoint scope
                self.fuzz_scope[path].append(seed_body_copy)

            # Adicionar novos paths ao escopo filtered_fuzz_scope
            if new_payload_paths:
                for new_path in new_payload_paths:
                    entry_copy = copy.deepcopy(seed_body)
                    entry_copy['path'] = new_path
                    entry_copy.update(
                        {
                            'spec_path':path,
                            'fuzz_rounds': len(new_payload_paths)
                        }
                    )
                    if new_path not in filtered_fuzz_scope:
                        filtered_fuzz_scope[new_path] = []
                    filtered_fuzz_scope[new_path].append(entry_copy)
            else:
                filtered_fuzz_scope[path] = self.fuzz_scope[path]

        if self.set_param_scope and not new_payload_paths:
            print()
            set_params = ','.join(self.set_param_scope)
            print(f"  {colored(f'No paths found with specified parameters: {set_params}', 99)}")
            print()
            sys.exit(1)

        # this should be enabled just in some aggressive fuzzing scenarios
        # it handles application/x-www-form-urlencoded parameters fuzzing
        # grant_type=$JCF-P&username=$JCF-R&password=$JCF-R&scope=$JCF-P&client_id=$JCF-P&client_secret=$JCF-P'
        self.expand_fuzz_scope(filtered_fuzz_scope)

        # Process the final fuzzing scope
        self.start_fuzzing(filtered_fuzz_scope)


    