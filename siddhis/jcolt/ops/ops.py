
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

from pygments import highlight, lexers, formatters
from neotermcolor import colored,cprint
from tabulate import tabulate
from ..cmd.list import jcList 
from ..utils import *
from time import sleep
import json
import re

class jcOps:
    def __init__(self, api_schema, vmnf_handler:False):
        self.api_specs = api_schema
        self.jc_list = jcList(api_schema)

        self.h_color = 95
        self.v_color = 99 
        self.align = 35

        self.colors_disabled = vmnf_handler.get('colors_disabled', False)

        if self.colors_disabled:
            self.h_color = None
            self.v_color = None
            self.align = 25
    
    def list_response_headers(self):
        response_headers = self.jc_list.list_response_headers()
        print(response_headers)

    def list_response_codes(self):
        if 'components' in self.api_specs:
            if 'responses' in self.api_specs['components']:
                responses = self.api_specs['components']['responses']
                cprint(f"\n{colored('Responses',self.h_color):>{self.align}}:")
                for code, response in responses.items():
                    print(f"\t{colored(code,self.v_color)}: {response['description']}")
        print()

    def list_descriptions(self):
        descriptions = self.jc_list.list_descriptions()
        headers=[
            colored("Path", 99, attrs=['bold']), 
            colored("Description", 99, attrs=['bold'])
        ]
        if not descriptions:
            print('No descriptions found')
            return
        
        desc_table = []
        for path, description in descriptions.items():
            # 49
            if description != 'No description provided':
                description = colored(description, 49)

            desc_table.append([
                path, 
                description
            ])

        print()
        print(tabulate(desc_table, headers=headers, tablefmt="fancy_grid"))
        print()

    def list_opids(self):
        print(f"\n    OperationIds:\n")
        op_ids = self.jc_list.list_opids()
        if op_ids:
            for oid in op_ids:
                print(f"       + {colored(oid.strip(),99):>17}")
                sleep(0.01)
            print()

    def list_tags(self):
        tags = self.jc_list.list_tags()
        if tags:
            cprint(f"\n{colored('Tags',self.h_color):>{self.align}}:")
            for tag in tags:
                print(f"\t{colored(tag,self.v_color)}")
        print()

    def list_examples(self):
        examples = self.jc_list.list_examples()
        if not examples:
            print()
            print('     → No examples found')
            print()
            return

        if examples:
            cprint(f"\n{colored('Examples',self.h_color):>{self.align}}:")
            for ex in examples:
                print(f"\t{colored(ex,self.v_color)}")
        print()

    def list_schemas(self):
        align = 12

        if 'components' in self.api_specs:
            securitySchemes = self.api_specs['components'].get('securitySchemes', False)

            if securitySchemes:
                cprint(f"\n{colored('SecuritySchemes',self.h_color):>{self.align}}:")
                json_dump = json.dumps(securitySchemes, indent=4)

                aligned_json_aligned = align_json(json_dump, align, self.v_color)
                print(aligned_json_aligned)

            if 'schemas' in self.api_specs['components']:
                cprint(f"\n{colored('Schemas',self.h_color):>{self.align}}:\n")
                schemas = self.jc_list.sort_list(self.api_specs['components']['schemas'])

                for sc in schemas:
                    print(f"\t\t{colored(sc,self.v_color)}")
        print()


    def list_field_constraints(self):
        """List all fields with their validation constraints, highlighting security risks."""
        models = self.jc_list.list_pydantic_models()
        
        table_data = []
        headers = ["Model.Field", "Type", "Constraints"]
        
        for name, model in models.items():
            for field_name, field in model.get('fields', {}).items():
                field_type = field.get('type', 'unknown')
                format_type = field.get('format')
                constraints = []
                
                if format_type:
                    field_type += f" ({format_type})"
                    constraints.append(f"format: {format_type}")
                    
                # Extract various constraints
                if 'minLength' in field.get('constraints', {}):
                    constraints.append(f"minLength: {field['constraints']['minLength']}")
                if 'maxLength' in field.get('constraints', {}):
                    constraints.append(f"maxLength: {field['constraints']['maxLength']}")
                if 'minimum' in field.get('constraints', {}):
                    constraints.append(f"minimum: {field['constraints']['minimum']}")
                if 'maximum' in field.get('constraints', {}):
                    constraints.append(f"maximum: {field['constraints']['maximum']}")
                if 'pattern' in field.get('constraints', {}):
                    constraints.append(f"pattern: {field['constraints']['pattern']}")
                if 'exclusiveMinimum' in field.get('constraints', {}):
                    constraints.append(f"exclusiveMinimum: {field['constraints']['exclusiveMinimum']}")
                
                # Highlight fields lacking constraints
                if not constraints and field_name.lower() in ['password', 'token', 'key', 'secret']:
                    constraints = ["NO CONSTRAINTS (⚠️ SECURITY RISK)"]
                elif not constraints:
                    constraints = ["No constraints"]
                
                table_data.append([
                    f"{name}.{field_name}", 
                    field_type, 
                    ", ".join(constraints)
                ])
        
        print("\nField constraints:")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        

    def list_endpoint_models(self):
        """Map API endpoints to their request and response models."""
        paths = self.api_specs.get('paths', {})
        
        table_data = []
        headers = ["Endpoint", "Method", "Request Model", "Response Model"]
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                # Get request model
                request_model = "None"
                if 'requestBody' in operation:
                    content = operation['requestBody'].get('content', {})
                    for content_type, content_schema in content.items():
                        if 'schema' in content_schema and '$ref' in content_schema['schema']:
                            ref = content_schema['schema']['$ref']
                            request_model = ref.split('/')[-1]
                
                # Get response model(s)
                response_models = []
                for status_code, response in operation.get('responses', {}).items():
                    if status_code.startswith('2'):  # Success responses
                        content = response.get('content', {})
                        for content_type, content_schema in content.items():
                            if 'schema' in content_schema:
                                schema = content_schema['schema']
                                if '$ref' in schema:
                                    response_models.append(schema['$ref'].split('/')[-1])
                                elif 'items' in schema and '$ref' in schema['items']:
                                    response_models.append(f"Array of {schema['items']['$ref'].split('/')[-1]}")
                
                response_model = ", ".join(response_models) if response_models else "None"
                
                table_data.append([
                    path,
                    method.upper(),
                    request_model,
                    response_model
                ])
        
        print("\n> Endpoint models:")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print()
        

    def list_validation_coverage(self):
        """Analyze models and fields for validation coverage."""
        models = self.jc_list.list_pydantic_models()
        
        table_data = []
        headers = ["Model", "Fields With Constraints", "Fields Missing Constraints", "Coverage %"]
        
        for name, model in models.items():
            fields = model.get('fields', {})
            fields_with_constraints = 0
            fields_without_constraints = 0
            
            for field_name, field in fields.items():
                has_constraints = False
                
                # Check various constraint types
                if field.get('format'):
                    has_constraints = True
                
                constraints = field.get('constraints', {})
                if constraints and any(c in constraints for c in [
                    'minLength', 'maxLength', 'pattern', 'minimum', 
                    'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
                    'multipleOf', 'minItems', 'maxItems', 'uniqueItems'
                ]):
                    has_constraints = True
                    
                if field.get('required'):
                    has_constraints = True
                    
                if has_constraints:
                    fields_with_constraints += 1
                else:
                    fields_without_constraints += 1
            
            total_fields = fields_with_constraints + fields_without_constraints
            coverage = 0 if total_fields == 0 else (fields_with_constraints / total_fields) * 100
            
            table_data.append([
                name,
                fields_with_constraints,
                fields_without_constraints,
                f"{coverage:.1f}%"
            ])
        
        print("\n> Validation coverage:")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print()
        
    def list_model_relationships(self):
        """Show model relationships and dependencies."""
        models = self.jc_list.list_pydantic_models()
        
        # Build a dependency graph
        dependency_graph = {}
        
        # Scan for references to other models
        for name, model in models.items():
            dependencies = set()
            
            # Extract dependencies from field schemas
            for field_name, field in model.get('fields', {}).items():
                schema = field.get('schema', {})
                if '$ref' in schema:
                    ref = schema['$ref'].split('/')[-1]
                    dependencies.add(ref)
                
                # Check for array item references
                if field.get('type') == 'array' and 'items' in schema:
                    items = schema['items']
                    if '$ref' in items:
                        ref = items['$ref'].split('/')[-1]
                        dependencies.add(ref)
            
            dependency_graph[name] = list(dependencies)
        
        # Format for output
        table_data = []
        headers = ["Model", "Dependencies"]
        
        for model, deps in dependency_graph.items():
            if deps:
                table_data.append([
                    model,
                    "→ " + ", ".join(deps)
                ])
            else:
                table_data.append([
                    model,
                    "No dependencies"
                ])
        
        print("\n> Model relationships:")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print()
        
    def list_enums(self):
        """List and analyze enum fields which are often overlooked during testing."""
        components = self.api_specs.get('components', {})
        schemas = components.get('schemas', {})
        
        table_data = []
        headers = ["Field", "Allowed Values"]
        
        # Find enum fields in schema definitions
        for schema_name, schema in schemas.items():
            # Check if schema itself is an enum
            if 'enum' in schema:
                values = schema['enum']
                table_data.append([
                    schema_name,
                    ", ".join([f'"{v}"' for v in values])
                ])
            
            # Check properties for enums
            for prop_name, prop in schema.get('properties', {}).items():
                if 'enum' in prop:
                    values = prop['enum']
                    table_data.append([
                        f"{schema_name}.{prop_name}",
                        ", ".join([f'"{v}"' for v in values])
                    ])
                    
                # Check for enums in referenced schemas
                if '$ref' in prop:
                    ref_name = prop['$ref'].split('/')[-1]
                    ref_schema = schemas.get(ref_name, {})
                    if 'enum' in ref_schema:
                        values = ref_schema['enum']
                        table_data.append([
                            f"{schema_name}.{prop_name} → {ref_name}",
                            ", ".join([f'"{v}"' for v in values])
                        ])
        
        print("\n> Enum fields:")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print()

    def list_security_fields(self):
        """Identify potentially security-sensitive fields in models."""
        models = self.jc_list.list_pydantic_models()
        
        table_data = []
        headers = ["Field", "Category", "Reason"]
        
        # Define patterns to identify sensitive fields
        sensitive_patterns = {
            'HIGH RISK': [
                ('password', r'.*password.*'),
                ('token', r'.*token.*'),
                ('key', r'.*(api_?key|secret_?key).*'),
                ('credential', r'.*(credential|secret).*')
            ],
            'PII': [
                ('email', r'.*email.*'),
                ('phone', r'.*phone.*'),
                ('address', r'.*address.*'),
                ('name', r'.*(first|last|full).*name'),
                ('ssn', r'.*(ssn|social.*security).*')
            ],
            'PCI DATA': [
                ('credit card', r'.*(card|credit|cvv|ccv).*'),
                ('account', r'.*(account|routing).*number')
            ]
        }
        
        for name, model in models.items():
            for field_name, field in model.get('fields', {}).items():
                field_type = field.get('type', 'unknown')
                format_type = field.get('format')
                
                # Check field against sensitive patterns
                for category, patterns in sensitive_patterns.items():
                    for pattern_name, pattern in patterns:
                        if re.search(pattern, field_name.lower()):
                            reason = f"Field name matches pattern for {pattern_name}"
                            table_data.append([
                                f"{name}.{field_name}",
                                category,
                                reason
                            ])
                            break
                
                # Check for fields with sensitive formats
                if format_type == 'password':
                    table_data.append([
                        f"{name}.{field_name}",
                        "HIGH RISK",
                        "Field has password format"
                    ])
                elif format_type == 'email':
                    table_data.append([
                        f"{name}.{field_name}",
                        "PII",
                        "Field has email format"
                    ])
        
        print("\n> Security-sensitive fields:")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print()
        
    def list_pydantic_models(self):
        models = self.jc_list.list_pydantic_models()
        if not models:
            print(" → No Pydantic models found in API specification")
            return
            
        print(f"\nFound {len(models)} Pydantic models in API specification:")
        
        from tabulate import tabulate

        table_data = []
        for name, model in models.items():
            field_count = len(model.get('fields', {}))
            required_fields = len(model.get('required', []))
            endpoint = model.get('path', 'N/A')
            table_data.append([name, field_count, required_fields, endpoint])
            
        headers = ["Model Name", "Fields", "Required", "Endpoint"]
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print()

    def list_parameters(self, path=None, raw_mode = False):        
        parameters = self.jc_list.list_parameters()

        if not parameters:
            print('No parameters found')
            return 

        print('\n\n\n')
            
        table_data = []
        headers=[
            colored("Path", 99, attrs=['bold']), 
            colored("Method", 99, attrs=['bold']),
            colored("Parameters", 99, attrs=['bold']),
            colored("Location", 99, attrs=['bold']),
            colored("Required", 99, attrs=['bold']),
            colored("Schema", 99, attrs=['bold'])         
        ]
        for path, methods in parameters.items():
            for method, params in methods.items():
                method = method.upper()
                if params:
                    for param in params:
                        schema = json.dumps(param['schema'],indent=2)
                        pretty_schema = highlight(schema, lexers.JsonLexer(), formatters.TerminalFormatter())
                        table_data.append([
                            path, 
                            method, 
                            param['name'], 
                            param['in'], 
                            param['required'], 
                            pretty_schema
                        ])
                else:
                    table_data.append([path, method, " ", " ", " ", " "])
                    
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))


