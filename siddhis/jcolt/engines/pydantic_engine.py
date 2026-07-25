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

import re
import json
import logging
import random
import string
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple
from urllib.parse import urlparse, urljoin
import asyncio
import aiohttp
import httpx
from mimesis import Generic
from ..engines.fetcher import jcfetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("jcolt.pydantic_engine")

class PydanticModelExtractor:
    """
    Extracts Pydantic models from OpenAPI schema for targeted testing.
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize the extractor with an OpenAPI schema.
        
        Args:
            schema: OpenAPI schema dictionary
        """
        self.schema = schema
        self.models = {}
        self.refs_cache = {}

    def extract_models(self):
        """
        Extract Pydantic models from the OpenAPI schema.
        
        Returns:
            Dict mapping model names to their schema definitions
        """
        if not self.schema or not isinstance(self.schema, dict):
            logger.error("Invalid schema format")
            return {}
            
        models = {}
        
        # Get schemas from components
        components = self.schema.get('components', {})
        schemas = components.get('schemas', {})
        
        logger.info(f"Found {len(schemas)} schema definitions in components")
        
        for name, schema_def in schemas.items():
            # Skip certain utility schemas
            if name in ['HTTPValidationError', 'ValidationError']:
                continue
                
            # Skip schemas that are just enums or don't have properties
            if 'properties' not in schema_def and 'enum' in schema_def:
                continue
                
            models[name] = {
                'name': name,
                'schema': schema_def,
                'fields': self._extract_fields(schema_def),
                'required': schema_def.get('required', [])
            }
            logger.debug(f"Extracted model: {name}")
            
        logger.info(f"Successfully extracted {len(models)} models")
        return models
    
    def _extract_fields(self, schema_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract fields from a schema definition.
        
        Args:
            schema_def: Schema definition
            
        Returns:
            Dictionary of field names to their definitions
        """
        fields = {}
        properties = schema_def.get('properties', {})
        
        for field_name, field_def in properties.items():
            # Resolve reference if present
            if '$ref' in field_def:
                ref = field_def['$ref']
                field_def = self._resolve_ref(ref)
                
            fields[field_name] = {
                'name': field_name,
                'type': field_def.get('type', 'string'),
                'format': field_def.get('format'),
                'required': field_name in schema_def.get('required', []),
                'constraints': self._extract_constraints(field_def),
                'enum': field_def.get('enum'),
                'schema': field_def
            }
            
        return fields
    
    def _extract_constraints(self, field_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract constraints from a field definition.
        
        Args:
            field_def: Field definition
            
        Returns:
            Dictionary of constraints
        """
        constraints = {}
        field_type = field_def.get('type', 'string')
        
        # Common constraints
        for constraint in ['default', 'pattern', 'format']:
            if constraint in field_def:
                constraints[constraint] = field_def[constraint]
                
        # String constraints
        if field_type == 'string':
            for constraint in ['minLength', 'maxLength']:
                if constraint in field_def:
                    constraints[constraint] = field_def[constraint]
                    
        # Numeric constraints
        elif field_type in ['number', 'integer']:
            for constraint in ['minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf']:
                if constraint in field_def:
                    constraints[constraint] = field_def[constraint]
                    
        # Array constraints
        elif field_type == 'array':
            for constraint in ['minItems', 'maxItems', 'uniqueItems']:
                if constraint in field_def:
                    constraints[constraint] = field_def[constraint]
            
            # Extract item constraints
            if 'items' in field_def:
                constraints['items'] = self._extract_constraints(field_def['items'])
                
        return constraints
    
    def _resolve_ref(self, ref: str) -> Dict[str, Any]:
        """
        Resolve a reference to its target schema.
        
        Args:
            ref: Reference string (e.g., "#/components/schemas/User")
            
        Returns:
            Resolved schema
        """
        if ref in self.refs_cache:
            return self.refs_cache[ref]
            
        if not ref.startswith('#/'):
            logger.warning(f"External references not supported: {ref}")
            return {'type': 'object'}
            
        path = ref[2:].split('/')
        current = self.schema
        
        try:
            for segment in path:
                current = current[segment]
                
            self.refs_cache[ref] = current
            return current
        except (KeyError, TypeError):
            logger.warning(f"Could not resolve reference: {ref}")
            return {'type': 'object'}
            
    def get_request_bodies(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract request body schemas and map them to their models.
        
        Returns:
            Dictionary mapping operation IDs to request body info
        """
        request_bodies = {}
        
        for path, path_item in self.schema.get('paths', {}).items():
            for method, operation in path_item.items():
                if method.lower() not in ['post', 'put', 'patch']:
                    continue
                    
                request_body = operation.get('requestBody', {})
                if not request_body:
                    continue
                    
                content = request_body.get('content', {})
                for content_type, content_schema in content.items():
                    if 'schema' in content_schema:
                        schema = content_schema['schema']
                        operation_id = operation.get('operationId', f"{method}_{path}")
                        model_name = None
                        
                        # If schema has a reference, extract the model name
                        if '$ref' in schema:
                            ref = schema['$ref']
                            parts = ref.split('/')
                            model_name = parts[-1]
                            
                        request_bodies[operation_id] = {
                            'path': path,
                            'method': method,
                            'content_type': content_type,
                            'schema': schema,
                            'model_name': model_name,
                            'required': request_body.get('required', False)
                        }
                        
                        if model_name:
                            logger.debug(f"Mapped {operation_id} to model {model_name}")
        
        logger.info(f"Extracted {len(request_bodies)} request bodies")
        return request_bodies


class PydanticTestVectorGenerator:
    """
    Generates test vectors for Pydantic model fields based on their type and constraints.
    """
    
    def __init__(self, models: Dict[str, Any], test_types: Optional[List[str]] = None):
        """
        Initialize the test vector generator.
        
        Args:
            models: Dictionary of models extracted by PydanticModelExtractor
            test_types: Optional list of test types to generate
        """
        self.models = models
        self.gen = Generic('en')
        self.test_types = test_types or [
            'type_confusion', 
            'validation_bypass', 
            'boundary_testing',
            'special_chars',
            'injection',
            'serialization'
        ]
        
    def generate_for_model(self, model_name: str) -> Dict[str, Any]:
        """
        Generate test vectors for all fields in a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary of field names to test vectors
        """
        if model_name not in self.models:
            logger.warning(f"Model not found: {model_name}")
            return {}
            
        model = self.models[model_name]
        result = {
            'model_name': model_name,
            'fields': {}
        }
        
        for field_name, field in model.get('fields', {}).items():
            result['fields'][field_name] = self.generate_for_field(field)
            
        return result
    
    def generate_for_field(self, field: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate test vectors for a specific field based on its type and constraints.
        
        Args:
            field: Field definition
            
        Returns:
            Test vectors for the field
        """
        result = {
            'field_name': field['name'],
            'field_type': field['type'],
            'tests': []
        }
        
        # Generate basic valid value for reference
        valid_value = self._generate_valid_value(field)
        result['valid_value'] = valid_value
        
        # Generate test vectors based on field type and enabled test types
        if 'type_confusion' in self.test_types:
            result['tests'].extend(self._generate_type_confusion_tests(field, valid_value))
            
        if 'validation_bypass' in self.test_types:
            # Use the schema field which contains the actual constraints
            schema_constraints = self._extract_constraints(field.get('schema', {}))
            # Create a field with proper constraints for test generation
            field_with_constraints = field.copy()
            field_with_constraints['constraints'] = schema_constraints
            result['tests'].extend(self._generate_validation_bypass_tests(field_with_constraints, valid_value))
            
        if 'boundary_testing' in self.test_types:
            result['tests'].extend(self._generate_boundary_tests(field, valid_value))
            
        if 'special_chars' in self.test_types:
            result['tests'].extend(self._generate_special_char_tests(field, valid_value))
            
        if 'injection' in self.test_types:
            result['tests'].extend(self._generate_injection_tests(field, valid_value))
            
        return result
    
    def _generate_valid_value(self, field: Dict[str, Any]) -> Any:
        """
        Generate a valid value for a field.
        
        Args:
            field: Field definition
            
        Returns:
            A valid value for the field
        """
        field_type = field['type']
        constraints = field.get('constraints', {})
        
        if field.get('enum'):
            # If field has enumerated values, pick one
            return random.choice(field['enum'])
        
        if field_type == 'string':
            format_type = field.get('format')
            
            if format_type == 'email':
                return self.gen.person.email()
            elif format_type == 'uri' or format_type == 'url':
                return self.gen.internet.url()
            elif format_type == 'date':
                return self.gen.datetime.date().isoformat()
            elif format_type == 'date-time':
                return self.gen.datetime.datetime().isoformat()
            elif format_type == 'uuid':
                return str(self.gen.random.uuid())
            elif format_type == 'password':
                return self.gen.person.password()
            else:
                # Regular string
                min_length = constraints.get('minLength', 5)
                max_length = constraints.get('maxLength', 20)
                length = min(max(min_length, 5), min(max_length, 20))
                
                # Check for pattern constraint
                pattern = constraints.get('pattern')
                if pattern:
                    try:
                        # Simplified approach for pattern matching
                        if 'email' in pattern.lower():
                            return self.gen.person.email()
                        elif 'url' in pattern.lower():
                            return self.gen.internet.url()
                        elif 'uuid' in pattern.lower():
                            return str(self.gen.random.uuid())
                        else:
                            # Default fallback
                            return self.gen.text.word()
                    except:
                        return self.gen.text.word()
                else:
                    return self.gen.text.word()
                    
        elif field_type == 'number' or field_type == 'integer':
            min_val = constraints.get('minimum', 0)
            max_val = constraints.get('maximum', 100)
            
            if field_type == 'integer':
                return random.randint(min_val, max_val)
            else:
                return round(random.uniform(min_val, max_val), 2)
                
        elif field_type == 'boolean':
            return random.choice([True, False])
            
        elif field_type == 'array':
            items_schema = field.get('items', {})
            min_items = constraints.get('minItems', 1)
            max_items = constraints.get('maxItems', 3)
            num_items = random.randint(min_items, min(max_items, 3))
            
            # Generate items based on schema
            if 'type' in items_schema:
                item_field = {
                    'type': items_schema['type'],
                    'constraints': constraints.get('items', {})
                }
                return [self._generate_valid_value(item_field) for _ in range(num_items)]
            else:
                return ["item"] * num_items
            
        elif field_type == 'object':
            return {"key": "value"}
                
        # Default fallback
        return None
    
    def _generate_type_confusion_tests(self, field: Dict[str, Any], valid_value: Any) -> List[Dict[str, Any]]:
        """
        Generate tests that attempt to confuse the type system.
        
        Args:
            field: Field definition
            valid_value: A valid value for reference
            
        Returns:
            List of test vectors targeting type confusion
        """
        tests = []
        field_type = field['type']
        field_name = field['name']
        
        if field_type == 'string':
            tests.append({
                'name': f"Type confusion - integer instead of string",
                'test_type': 'type_confusion',
                'value': 12345,
                'expected_result': 'REJECTED',
                'description': "Send an integer where a string is expected"
            })
            tests.append({
                'name': f"Type confusion - object instead of string",
                'test_type': 'type_confusion',
                'value': {"nested": "value"},
                'expected_result': 'REJECTED',
                'description': "Send an object where a string is expected"
            })
            
        elif field_type == 'number' or field_type == 'integer':
            tests.append({
                'name': f"Type confusion - string instead of number",
                'test_type': 'type_confusion',
                'value': "12345",
                'expected_result': 'REJECTED' if field_type == 'integer' else 'ACCEPTED',
                'description': f"Send a string where a {field_type} is expected"
            })
            tests.append({
                'name': f"Type confusion - numeric string with letters",
                'test_type': 'type_confusion',
                'value': "123abc",
                'expected_result': 'REJECTED',
                'description': f"Send a string with letters where a {field_type} is expected"
            })
            
        elif field_type == 'boolean':
            tests.append({
                'name': f"Type confusion - integer instead of boolean",
                'test_type': 'type_confusion',
                'value': 1,
                'expected_result': 'ACCEPTED',
                'description': "Send 1 where a boolean is expected (should be coerced to true)"
            })
            tests.append({
                'name': f"Type confusion - string instead of boolean",
                'test_type': 'type_confusion',
                'value': "true",
                'expected_result': 'REJECTED',
                'description': "Send string 'true' where a boolean is expected"
            })
            
        elif field_type == 'array':
            tests.append({
                'name': f"Type confusion - object instead of array",
                'test_type': 'type_confusion',
                'value': {"0": "item"},
                'expected_result': 'REJECTED',
                'description': "Send an object where an array is expected"
            })
            tests.append({
                'name': f"Type confusion - string instead of array",
                'test_type': 'type_confusion',
                'value': "[]",
                'expected_result': 'REJECTED',
                'description': "Send a string representation where an array is expected"
            })
            
        elif field_type == 'object':
            tests.append({
                'name': f"Type confusion - array instead of object",
                'test_type': 'type_confusion',
                'value': ["item"],
                'expected_result': 'REJECTED',
                'description': "Send an array where an object is expected"
            })
            tests.append({
                'name': f"Type confusion - string instead of object",
                'test_type': 'type_confusion',
                'value': "{}",
                'expected_result': 'REJECTED',
                'description': "Send a string representation where an object is expected"
            })
            
        return tests
    
    def _generate_validation_bypass_tests(self, field: Dict[str, Any], valid_value: Any) -> List[Dict[str, Any]]:
        """
        Generate tests that attempt to bypass validation rules.
        
        Args:
            field: Field definition
            valid_value: A valid value for reference
            
        Returns:
            List of test vectors targeting validation bypasses
        """
        tests = []
        field_type = field['type']
        constraints = field.get('constraints', {})
        format_type = field.get('format')
        
        if field_type == 'string':
            # Test pattern bypasses
            if 'pattern' in constraints:
                pattern = constraints['pattern']
                
                if format_type == 'email' or 'email' in pattern.lower():
                    tests.append({
                        'name': "Email validation bypass - null byte",
                        'test_type': 'validation_bypass',
                        'value': "user@example.com%00malicious",
                        'expected_result': 'REJECTED',
                        'description': "Try to bypass email validation with null byte"
                    })
                    tests.append({
                        'name': "Email validation bypass - unusual TLD",
                        'test_type': 'validation_bypass',
                        'value': "user@example.attackercontrolled",
                        'expected_result': 'REJECTED',
                        'description': "Try to bypass email validation with unusual TLD"
                    })
                    
                elif format_type == 'uri' or format_type == 'url' or 'url' in pattern.lower():
                    tests.append({
                        'name': "URL validation bypass - javascript URL",
                        'test_type': 'validation_bypass',
                        'value': "javascript:alert(1)",
                        'expected_result': 'REJECTED',
                        'description': "Try to bypass URL validation with javascript: protocol"
                    })
                    tests.append({
                        'name': "URL validation bypass - data URL",
                        'test_type': 'validation_bypass',
                        'value': "data:text/html,<script>alert(1)</script>",
                        'expected_result': 'REJECTED',
                        'description': "Try to bypass URL validation with data: protocol"
                    })
            
            # Test length bypasses
            if 'minLength' in constraints:
                min_length = constraints['minLength']
                if min_length > 1:
                    tests.append({
                        'name': f"MinLength bypass - just below minimum",
                        'test_type': 'validation_bypass',
                        'value': "a" * (min_length - 1),
                        'expected_result': 'REJECTED',
                        'description': f"Try to bypass minLength={min_length} with fewer characters"
                    })
            
            if 'maxLength' in constraints:
                max_length = constraints['maxLength']
                tests.append({
                    'name': f"MaxLength bypass - just above maximum",
                    'test_type': 'validation_bypass',
                    'value': "a" * (max_length + 1),
                    'expected_result': 'REJECTED',
                    'description': f"Try to bypass maxLength={max_length} with more characters"
                })
                
        elif field_type in ['number', 'integer']:
            # Test numeric constraints
            if 'minimum' in constraints:
                min_value = constraints['minimum']
                tests.append({
                    'name': f"Minimum constraint bypass",
                    'test_type': 'validation_bypass',
                    'value': min_value - 1,
                    'expected_result': 'REJECTED',
                    'description': f"Try to bypass minimum={min_value} constraint"
                })
                
            if 'maximum' in constraints:
                max_value = constraints['maximum']
                tests.append({
                    'name': f"Maximum constraint bypass",
                    'test_type': 'validation_bypass',
                    'value': max_value + 1,
                    'expected_result': 'REJECTED',
                    'description': f"Try to bypass maximum={max_value} constraint"
                })
                
            if 'multipleOf' in constraints:
                multiple_of = constraints['multipleOf']
                tests.append({
                    'name': f"MultipleOf constraint bypass",
                    'test_type': 'validation_bypass',
                    'value': multiple_of * 3 + 1,  # Not a multiple
                    'expected_result': 'REJECTED',
                    'description': f"Try to bypass multipleOf={multiple_of} constraint"
                })
                
        elif field_type == 'array':
            # Test array constraints
            if 'minItems' in constraints:
                min_items = constraints['minItems']
                if min_items > 0:
                    tests.append({
                        'name': f"MinItems constraint bypass",
                        'test_type': 'validation_bypass',
                        'value': [] if min_items > 0 else ["item"],
                        'expected_result': 'REJECTED',
                        'description': f"Try to bypass minItems={min_items} constraint"
                    })
                    
            if 'maxItems' in constraints:
                max_items = constraints['maxItems']
                tests.append({
                    'name': f"MaxItems constraint bypass",
                    'test_type': 'validation_bypass',
                    'value': ["item"] * (max_items + 1),
                    'expected_result': 'REJECTED',
                    'description': f"Try to bypass maxItems={max_items} constraint"
                })
                
            if constraints.get('uniqueItems', False):
                tests.append({
                    'name': f"UniqueItems constraint bypass",
                    'test_type': 'validation_bypass',
                    'value': ["duplicate", "duplicate"],
                    'expected_result': 'REJECTED',
                    'description': "Try to bypass uniqueItems constraint"
                })
                
        return tests
    
    def _generate_boundary_tests(self, field: Dict[str, Any], valid_value: Any) -> List[Dict[str, Any]]:
        """
        Generate tests that target boundary conditions.
        
        Args:
            field: Field definition
            valid_value: A valid value for reference
            
        Returns:
            List of test vectors targeting boundary conditions
        """
        tests = []
        field_type = field['type']
        constraints = field.get('constraints', {})
        
        if field_type == 'string':
            # Test string length boundaries
            if 'minLength' in constraints:
                min_length = constraints['minLength']
                
                if min_length > 0:
                    tests.append({
                        'name': f"String boundary - exactly minLength",
                        'test_type': 'boundary_testing',
                        'value': "a" * min_length,
                        'expected_result': 'ACCEPTED',
                        'description': f"String with exactly the minimum length ({min_length})"
                    })
                    
                    if min_length > 1:
                        tests.append({
                            'name': f"String boundary - minLength - 1",
                            'test_type': 'boundary_testing',
                            'value': "a" * (min_length - 1),
                            'expected_result': 'REJECTED',
                            'description': f"String with length one less than minimum ({min_length-1})"
                        })
                        
            if 'maxLength' in constraints:
                max_length = constraints['maxLength']
                
                tests.append({
                    'name': f"String boundary - exactly maxLength",
                    'test_type': 'boundary_testing',
                    'value': "a" * max_length,
                    'expected_result': 'ACCEPTED',
                    'description': f"String with exactly the maximum length ({max_length})"
                })
                
                tests.append({
                    'name': f"String boundary - maxLength + 1",
                    'test_type': 'boundary_testing',
                    'value': "a" * (max_length + 1),
                    'expected_result': 'REJECTED',
                    'description': f"String with length one more than maximum ({max_length+1})"
                })
                
        elif field_type in ['number', 'integer']:
            # Test numeric boundaries
            if 'minimum' in constraints:
                min_value = constraints['minimum']
                
                tests.append({
                    'name': f"Numeric boundary - exactly minimum",
                    'test_type': 'boundary_testing',
                    'value': min_value,
                    'expected_result': 'ACCEPTED',
                    'description': f"Value exactly at the minimum ({min_value})"
                })
                
                tests.append({
                    'name': f"Numeric boundary - just below minimum",
                    'test_type': 'boundary_testing',
                    'value': min_value - (0.1 if field_type == 'number' else 1),
                    'expected_result': 'REJECTED',
                    'description': f"Value just below the minimum"
                })
                
            if 'maximum' in constraints:
                max_value = constraints['maximum']
                
                tests.append({
                    'name': f"Numeric boundary - exactly maximum",
                    'test_type': 'boundary_testing',
                    'value': max_value,
                    'expected_result': 'ACCEPTED',
                    'description': f"Value exactly at the maximum ({max_value})"
                })
                
                tests.append({
                    'name': f"Numeric boundary - just above maximum",
                    'test_type': 'boundary_testing',
                    'value': max_value + (0.1 if field_type == 'number' else 1),
                    'expected_result': 'REJECTED',
                    'description': f"Value just above the maximum"
                })
                
            # Test exclusive boundaries
            if 'exclusiveMinimum' in constraints:
                ex_min = constraints['exclusiveMinimum']
                
                tests.append({
                    'name': f"Numeric boundary - exactly exclusiveMinimum",
                    'test_type': 'boundary_testing',
                    'value': ex_min,
                    'expected_result': 'REJECTED',
                    'description': f"Value exactly at the exclusive minimum ({ex_min})"
                })
                
                tests.append({
                    'name': f"Numeric boundary - just above exclusiveMinimum",
                    'test_type': 'boundary_testing',
                    'value': ex_min + (0.1 if field_type == 'number' else 1),
                    'expected_result': 'ACCEPTED',
                    'description': f"Value just above the exclusive minimum"
                })
                
            if 'exclusiveMaximum' in constraints:
                ex_max = constraints['exclusiveMaximum']
                
                tests.append({
                    'name': f"Numeric boundary - exactly exclusiveMaximum",
                    'test_type': 'boundary_testing',
                    'value': ex_max,
                    'expected_result': 'REJECTED',
                    'description': f"Value exactly at the exclusive maximum ({ex_max})"
                })
                
                tests.append({
                    'name': f"Numeric boundary - just below exclusiveMaximum",
                    'test_type': 'boundary_testing',
                    'value': ex_max - (0.1 if field_type == 'number' else 1),
                    'expected_result': 'ACCEPTED',
                    'description': f"Value just below the exclusive maximum"
                })
                
        elif field_type == 'array':
            # Test array length boundaries
            if 'minItems' in constraints:
                min_items = constraints['minItems']
                
                if min_items > 0:
                    tests.append({
                        'name': f"Array boundary - exactly minItems",
                        'test_type': 'boundary_testing',
                        'value': ["item"] * min_items,
                        'expected_result': 'ACCEPTED',
                        'description': f"Array with exactly the minimum items ({min_items})"
                    })
                    
                    if min_items > 1:
                        tests.append({
                            'name': f"Array boundary - minItems - 1",
                            'test_type': 'boundary_testing',
                            'value': ["item"] * (min_items - 1),
                            'expected_result': 'REJECTED',
                            'description': f"Array with one less than minimum items ({min_items-1})"
                        })
                        
            if 'maxItems' in constraints:
                max_items = constraints['maxItems']
                
                tests.append({
                    'name': f"Array boundary - exactly maxItems",
                    'test_type': 'boundary_testing',
                    'value': ["item"] * max_items,
                    'expected_result': 'ACCEPTED',
                    'description': f"Array with exactly the maximum items ({max_items})"
                })
                
                tests.append({
                    'name': f"Array boundary - maxItems + 1",
                    'test_type': 'boundary_testing',
                    'value': ["item"] * (max_items + 1),
                    'expected_result': 'REJECTED',
                    'description': f"Array with one more than maximum items ({max_items+1})"
                })
                
        return tests
    
    def _generate_special_char_tests(self, field: Dict[str, Any], valid_value: Any) -> List[Dict[str, Any]]:
        """
        Generate tests with special characters that might cause issues.
        
        Args:
            field: Field definition
            valid_value: A valid value for reference
            
        Returns:
            List of test vectors with special characters
        """
        tests = []
        field_type = field['type']
        
        if field_type == 'string':
            # Common special characters that might cause issues
            special_chars = [
                {
                    'name': "Special chars - null byte",
                    'value': "test\0test",
                    'description': "String with null byte"
                },
                {
                    'name': "Special chars - control characters",
                    'value': "test\n\r\ttest",
                    'description': "String with newlines, tabs and carriage returns"
                },
                {
                    'name': "Special chars - Unicode RTL override",
                    'value': "test\u202eoverflow",
                    'description': "String with Right-to-Left override character"
                },
                {
                    'name': "Special chars - Unicode homoglyphs",
                    'value': "рaypal.com",  # Cyrillic 'р' instead of Latin 'p'
                    'description': "String with Unicode homoglyphs (look-alike characters)"
                },
                {
                    'name': "Special chars - Emoji",
                    'value': "test 😀 test",
                    'description': "String with emoji characters"
                }
            ]
            
            for char_test in special_chars:
                tests.append({
                    'name': char_test['name'],
                    'test_type': 'special_chars',
                    'value': char_test['value'],
                    'expected_result': 'ACCEPTED',  # Most modern frameworks should handle these
                    'description': char_test['description']
                })
                
        elif field_type == 'object':
            # Test special characters in object keys
            tests.append({
                'name': "Special chars - object key with dot",
                'test_type': 'special_chars',
                'value': {"key.with.dots": "value"},
                'expected_result': 'ACCEPTED',
                'description': "Object with dots in key name (might affect ORM/path parsing)"
            })
            
            tests.append({
                'name': "Special chars - object key with unicode",
                'test_type': 'special_chars',
                'value': {"测试": "value"},
                'expected_result': 'ACCEPTED',
                'description': "Object with Unicode key name"
            })
            
        return tests
    
    def _generate_injection_tests(self, field: Dict[str, Any], valid_value: Any) -> List[Dict[str, Any]]:
        """
        Generate tests that attempt various injection attacks.
        
        Args:
            field: Field definition
            valid_value: A valid value for reference
            
        Returns:
            List of test vectors targeting injection vulnerabilities
        """
        tests = []
        field_type = field['type']
        format_type = field.get('format')
        
        if field_type == 'string':
            # SQL Injection tests
            sql_injections = [
                {
                    'name': "SQL Injection - basic",
                    'value': "' OR '1'='1",
                    'description': "Basic SQL injection attempt"
                },
                {
                    'name': "SQL Injection - comment",
                    'value': "'; SELECT NULL; --", 
                    'description': "SQL injection with comment"
                }
            ]
            
            for injection in sql_injections:
                tests.append({
                    'name': injection['name'],
                    'test_type': 'injection',
                    'value': injection['value'],
                    'expected_result': 'SANITIZED',  # Should be accepted but sanitized
                    'description': injection['description']
                })
            
            # XSS tests
            if format_type != 'password' and format_type != 'binary':
                xss_tests = [
                    {
                        'name': "XSS - basic",
                        'value': "<script>alert(1)</script>",
                        'description': "Basic XSS attempt"
                    },
                    {
                        'name': "XSS - HTML encoded",
                        'value': "&lt;script&gt;alert(1)&lt;/script&gt;",
                        'description': "HTML-encoded XSS attempt"
                    },
                    {
                        'name': "XSS - JavaScript event",
                        'value': "<img src=x onerror=alert(1)>",
                        'description': "XSS attempt using event handler"
                    }
                ]
                
                for injection in xss_tests:
                    tests.append({
                        'name': injection['name'],
                        'test_type': 'injection',
                        'value': injection['value'],
                        'expected_result': 'SANITIZED',  # Should be accepted but sanitized
                        'description': injection['description']
                    })
                    
        return tests


class PydanticTestRunner:
    """
    Runs the generated test vectors against the API and analyzes the results.
    """
    
    def __init__(self, target_url: str, models: Dict[str, Any], request_bodies: Dict[str, Any], **kwargs):
        """
        Initialize the test runner.
        
        Args:
            target_url: Base URL of the API
            models: Dictionary of models extracted by PydanticModelExtractor
            request_bodies: Dictionary of request bodies
            **kwargs: Additional configuration options
        """
        self.target_url = target_url.rstrip('/')
        self.models = models
        self.request_bodies = request_bodies
        self.kwargs = kwargs
        self.results = {}
        
        # Configure request options
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add authentication headers if provided
        if 'jwt_token' in kwargs and kwargs['jwt_token']:
            self.headers['Authorization'] = f"Bearer {kwargs['jwt_token']}"
            logger.info("Using JWT token for authentication")
            
        # Configure the fetcher
        self.fetcher_kwargs = {
            'target_url': target_url,
            'timeout': kwargs.get('timeout', 30),
            'max_retries': kwargs.get('max_retries', 2),
            'retry_delay': kwargs.get('retry_delay', 1),
            'verify_ssl': kwargs.get('verify_ssl', False),
            'debug_logging': kwargs.get('debug_logging', False),
            'headers': self.headers,
            'pydantic_test': kwargs.get('pydantic_test', True)
        }
        
        # Pass auth params to fetcher
        for auth_key in [
            'auth_type', 'auth_token', 'auth_refresh_token', 'auth_url',
            'username', 'password', 'client_id', 'client_secret',
            'token_url', 'scope', 'api_key', 'api_key_header',
            'api_key_in_query', 'api_key_param_name', 'login_url',
            'username_field', 'password_field', 'jwt_token'
        ]:
            if auth_key in kwargs and kwargs[auth_key]:
                self.fetcher_kwargs[auth_key] = kwargs[auth_key]
        
        logger.info(f"PydanticTestRunner initialized for {target_url}")
    
    async def run_tests(self, generator: PydanticTestVectorGenerator, model_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run tests for the specified models.
        
        Args:
            generator: Test vector generator
            model_names: Optional list of model names to test, if None test all models
            
        Returns:
            Dictionary of test results
        """
        
        if not model_names:
            # If no models specified, test all models
            model_names = list(self.models.keys())
            
        # Create a mapping of models to testable operations
        testable_models = []
        request_mapping = {}
        
        for operation_id, req_body in self.request_bodies.items():
            model_name = req_body.get('model_name')
            schema = req_body['schema']
            
            if model_name and model_name in model_names:
                print(f"Testing model: {model_name}")
                # This operation uses a model we want to test
                testable_models.append(model_name)
                request_mapping[model_name] = {
                    'operation_id': operation_id,
                    'path': req_body['path'],
                    'method': req_body['method'],
                    'content_type': req_body['content_type']
                }
                logger.info(f"Found testable endpoint for model {model_name}: {req_body['method'].upper()} {req_body['path']}")
            elif '$ref' in schema:
                # Extract model name from reference
                ref = schema['$ref']
                ref_parts = ref.split('/')
                ref_model_name = ref_parts[-1]
                
                if ref_model_name in model_names:
                    testable_models.append(ref_model_name)
                    request_mapping[ref_model_name] = {
                        'operation_id': operation_id,
                        'path': req_body['path'],
                        'method': req_body['method'],
                        'content_type': req_body['content_type']
                    }
                    logger.info(f"Found testable endpoint for model {ref_model_name}: {req_body['method'].upper()} {req_body['path']}")
        
        # Deduplicate the list
        testable_models = list(set(testable_models))
        
        if not testable_models:
            logger.warning("No testable models found with API endpoints")
            return {}
            
        logger.info(f"Testing {len(testable_models)} models with API endpoints")
            
        # Generate and run tests for each model
        for model_name in testable_models:
            logger.info(f"Running tests for model: {model_name}")
            
            # Generate test vectors
            test_vectors = generator.generate_for_model(model_name)
            
            # Get request information
            if model_name in request_mapping:
                req_info = request_mapping[model_name]
                
                # Run tests for this model
                model_results = await self._run_model_tests(model_name, test_vectors, req_info)
                
                # Store results
                self.results[model_name] = model_results
                logger.info(f"Completed testing model: {model_name}")
            else:
                logger.warning(f"No request mapping found for model: {model_name}")
            
        return self.results
    
    async def _run_model_tests(self, model_name: str, test_vectors: Dict[str, Any], req_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run tests for a specific model.
        
        Args:
            model_name: Name of the model
            test_vectors: Test vectors for the model
            req_info: Request information (path, method, etc.)
            
        Returns:
            Dictionary of test results for the model
        """
        logger.debug(f"Starting model tests for {model_name}")
        results = {
            'model_name': model_name,
            'path': req_info['path'],
            'method': req_info['method'],
            'operation_id': req_info['operation_id'],
            'fields': {}
        }
        
        for field_name, field_tests in test_vectors.get('fields', {}).items():
            field_results = []
            
            # Get valid value as baseline
            valid_value = field_tests.get('valid_value')
            
            # Run the baseline test first
            baseline_result = await self._run_single_test(
                model_name,
                field_name,
                {
                    'name': "Baseline valid value",
                    'test_type': 'baseline',
                    'value': valid_value,
                    'expected_result': 'ACCEPTED',
                    'description': "Baseline test with valid value"
                },
                req_info,
                test_vectors['fields']
            )
            
            field_results.append(baseline_result)
            
            # Run each test
            for test in field_tests.get('tests', []):
                test_result = await self._run_single_test(
                    model_name,
                    field_name,
                    test,
                    req_info,
                    test_vectors['fields']
                )
                
                field_results.append(test_result)
            
            results['fields'][field_name] = field_results
            
        return results
    
    async def _run_single_test(self, model_name: str, field_name: str, test: Dict[str, Any], 
                              req_info: Dict[str, Any], all_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single test for a field.
        
        Args:
            model_name: Name of the model
            field_name: Name of the field
            test: Test definition
            req_info: Request information
            all_fields: All fields in the model for building the request body
            
        Returns:
            Test result
        """
        logger.debug(f"Running test: {test['name']} for {model_name}.{field_name}")
        
        # Build request body with valid values for all fields
        # except the one being tested
        request_body = {}
        
        for f_name, f_tests in all_fields.items():
            if f_name == field_name:
                # Use the test value for this field
                request_body[f_name] = test['value']
            else:
                # Use valid value for other fields
                request_body[f_name] = f_tests.get('valid_value')
        
        # Create a request for the fetcher
        path = req_info['path']
        method = req_info['method']
        
        # Prepare a single request for the fetcher
        fuzz_scope = [{
            'properties': {
                'summary': f"Test {model_name}.{field_name} - {test['name']}",
                'operationId': req_info['operation_id'],
                'responses': {}  # We could extract expected responses here
            },
            'method': method,
            'host': self.target_url,
            'path': path,
            'body': request_body
        }]
        
        # Create fetcher and run
        fetcher = jcfetcher(fuzz_scope, **self.fetcher_kwargs)
        try:
            await fetcher.start_async()
            
            # Get results
            fuzz_results = fetcher.fuzz_results
        except Exception as e:
            logger.error(f"Error running test {test['name']} for {model_name}.{field_name}: {e}")
            # Create a failure result
            return {
                'name': test['name'],
                'test_type': test['test_type'],
                'value': test['value'],
                'expected_result': test['expected_result'],
                'description': test['description'],
                'actual_result': 'ERROR',
                'status_code': None,
                'response_body': None,
                'pass': False,
                'error': str(e)
            }
        
        # Process results
        if path in fuzz_results and fuzz_results[path]:
            response_data = fuzz_results[path][0]
            response = response_data.get('response')
            
            result = {
                'name': test['name'],
                'test_type': test['test_type'],
                'value': test['value'],
                'expected_result': test['expected_result'],
                'description': test['description'],
                'actual_result': None,
                'status_code': None,
                'response_body': None,
                'pass': False
            }
            
            if response:
                status_code = response.status
                result['status_code'] = status_code
                
                # Convert response text
                response_text = response_data.get('response_text')
                if response_text:
                    if isinstance(response_text, str):
                        try:
                            response_body = json.loads(response_text)
                        except json.JSONDecodeError:
                            response_body = response_text
                    else:
                        response_body = response_text
                    
                    result['response_body'] = response_body
                
                # Determine actual result based on status code
                if status_code < 400:
                    result['actual_result'] = 'ACCEPTED'
                elif status_code == 422:
                    result['actual_result'] = 'REJECTED'
                else:
                    result['actual_result'] = 'ERROR'
                
                # Check if test passed based on expected vs actual
                expected = test['expected_result']
                actual = result['actual_result']
                
                if expected == 'ACCEPTED' and actual == 'ACCEPTED':
                    result['pass'] = True
                elif expected == 'REJECTED' and actual == 'REJECTED':
                    result['pass'] = True
                elif expected == 'SANITIZED':
                    # For sanitized, we need to look at the response body
                    # This is a simplified check - in reality, would need more complex logic
                    if actual == 'ACCEPTED':
                        # Consider it a pass if accepted (assuming sanitization happened)
                        result['pass'] = True
                        result['note'] = "Accepted but sanitization status unknown"
                
            else:
                result['actual_result'] = 'ERROR'
                result['status_code'] = 0
                
            return result
        else:
            # No results found
            return {
                'name': test['name'],
                'test_type': test['test_type'],
                'value': test['value'],
                'expected_result': test['expected_result'],
                'description': test['description'],
                'actual_result': 'ERROR',
                'status_code': None,
                'response_body': None,
                'pass': False,
                'error': "No response received"
            }


class PydanticTester:
    """
    Main class for Pydantic model testing.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the Pydantic tester.
        
        Args:
            **kwargs: Configuration options
        """
        self.kwargs = kwargs
        self.schema = kwargs.get('schema')
        self.target_url = kwargs.get('target_url')
        self.model_extractor = None
        self.test_vector_generator = None
        self.test_runner = None
        self.results = {}
        self.models = {}
        self.request_bodies = {}
        self.api_testing_enabled = True
        
        # Initialize test state
        self.test_cases = {}
        
        logger.info(f"Initializing PydanticTester for {self.target_url}")

    async def setup(self) -> bool:
        """
        Setup the tester by extracting models and request bodies.
        
        Returns:
            True if setup was successful
        """
        try:
            # Validate prerequisites
            if not self.schema:
                logger.error("No schema provided")
                return False
            
            if not self.target_url:
                logger.error("No target URL provided")
                return False
                
            logger.info(f"Setting up Pydantic tester for target URL: {self.target_url}")
            
            # Set up headers for requests
            self.headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Configure authentication
            if 'jwt_token' in self.kwargs and self.kwargs['jwt_token']:
                self.headers['Authorization'] = f"Bearer {self.kwargs['jwt_token']}"
                logger.info("JWT token configured for authentication")
                print(f"JWT token configured for authentication: {self.kwargs['jwt_token'][:5]}")
            

            # Try to connect to the target to verify it's reachable
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{self.target_url}/health", 
                        headers=self.headers
                    )
                    logger.info(f"Target health check status: {response.status_code}")
                    print(f"Target health check status: {response.status_code}")
                    
                    if response.status_code != 200:
                        logger.warning(f"Health check returned status {response.status_code}")
                        print(f"Health check returned status {response.status_code}")

            except Exception as e:
                logger.warning(f"Target health check failed: {str(e)}")
                logger.warning("Continuing setup, but API requests may fail")
                print(f"Target health check failed: {str(e)}")
                
            # Extract models from schema
            logger.info("Extracting Pydantic models from schema")
            self.model_extractor = PydanticModelExtractor(self.schema)
            self.models = self.model_extractor.extract_models()
            logger.info(f"Extracted {len(self.models)} models from schema")
            print(f"Extracted {len(self.models)} models from schema")
            
            # Extract request bodies
            self.request_bodies = self.model_extractor.get_request_bodies()
            logger.info(f"Extracted {len(self.request_bodies)} request bodies")
            print(f"Extracted {len(self.request_bodies)} request bodies")
            
            # Map models to API endpoints
            testable_models = []
            
            for operation_id, req_body in self.request_bodies.items():
                model_name = req_body.get('model_name')
                schema = req_body['schema']
                
                if model_name and model_name in self.models:
                    testable_models.append(model_name)
                    logger.info(f"Mapped {operation_id} to model {model_name}")
                elif '$ref' in schema:
                    # Extract model name from reference
                    ref = schema['$ref']
                    ref_parts = ref.split('/')
                    ref_model_name = ref_parts[-1]
                    
                    if ref_model_name in self.models:
                        testable_models.append(ref_model_name)
                        # Update the request body with the model name
                        self.request_bodies[operation_id]['model_name'] = ref_model_name
                        logger.info(f"Mapped {operation_id} to model {ref_model_name} via $ref")
                        print(f"Mapped {operation_id} to model {ref_model_name} via $ref")
            

            # Remove duplicates
            testable_models = list(set(testable_models))
            logger.info(f"Found {len(testable_models)} testable models with API endpoints")
            print(f"Found {len(testable_models)} testable models with API endpoints")

            # Create test vector generator
            self.test_vector_generator = PydanticTestVectorGenerator(
                self.models,
                self.kwargs.get('pydantic_test_types', [
                    'type_confusion', 
                    'validation_bypass', 
                    'boundary_testing',
                    'special_chars',
                    'injection'
                ])
            )
            

            self.kwargs.pop('target_url')
            # Initialize the test runner
            self.test_runner = PydanticTestRunner(
                self.target_url,
                self.models,
                self.request_bodies,
                **self.kwargs
            )
            
            # Initialize test cases container
            self.test_cases = {}

            # Setup is successful if we have models and request bodies
            setup_success = len(self.models) > 0 and len(self.request_bodies) > 0
            
            if setup_success:
                logger.info(f"Setup completed successfully with {len(testable_models)} testable models")
                print(f"Setup completed successfully with {len(testable_models)} testable models")
            else:
                logger.warning("Setup completed with warnings - no testable models found")
                print("Setup completed with warnings - no testable models found")
                
            return setup_success
                
        except Exception as e:
            logger.error(f"Unhandled exception during setup: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
        
    async def run_tests(self) -> Dict[str, Any]:
        """
        Run tests for all testable models.
        
        Returns:
            Dictionary of test results
        """
        try:
            # Make sure we're set up
            if not self.test_runner or not self.test_vector_generator:
                setup_success = await self.setup()
                if not setup_success:
                    print("Setup failed, cannot run tests")
                    logger.error("Setup failed, cannot run tests")
                    return {}
            
            # Get list of model names to test
            model_filter = self.kwargs.get('pydantic_models', [])
            if model_filter and isinstance(model_filter, str):
                model_filter = [m.strip() for m in model_filter.split(',')]
                
            logger.info(f"Running tests with filter: {model_filter if model_filter else 'all models'}")
            
            # Run the tests
            self.results = await self.test_runner.run_tests(
                self.test_vector_generator,
                model_filter if model_filter else None
            )
            
            return self.results
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            logger.debug(traceback.format_exc())
            return {}


def run_pydantic_tests(vmnf_handler: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point function for running Pydantic tests from JColt.
    
    Args:
        vmnf_handler: Vimana framework handler
        
    Returns:
        Dictionary of test results
    """
    schema = vmnf_handler.get('schema')
    target_url = vmnf_handler.get('target_url')
    verbose = vmnf_handler.get('verbose', False)
    debug_logging = vmnf_handler.get('debug_logging', False)

    if not schema:
        logger.error("No schema provided")
        return {}

    if not target_url:
        # Try to extract URL from schema info
        if 'info' in schema and 'host' in schema['info']:
            target_url = schema['info']['host']
            vmnf_handler['target_url'] = target_url
            logger.info(f"Using URL from schema info: {target_url}")
        elif 'servers' in schema and schema['servers']:
            # OpenAPI 3.0 uses 'servers' array
            server_url = schema['servers'][0].get('url')
            if server_url:
                target_url = server_url
                vmnf_handler['target_url'] = target_url
                logger.info(f"Using URL from schema servers: {target_url}")
        else:
            logger.error("No target URL provided and couldn't extract from schema")
            return {}
    
    if verbose:
        print("Examining OpenAPI schema structure:")
        print(f"  Schema version: {schema.get('openapi', 'unknown')}")
        print(f"  Info: {schema.get('info', {}).get('title', 'unknown')}")
        if 'components' in schema:
            print(f"  Components: {list(schema.get('components', {}).keys())}")
            if 'schemas' in schema.get('components', {}):
                schemas = schema.get('components', {}).get('schemas', {})
                print(f"  Found {len(schemas)} schema definitions")
                if verbose:# and debug_logging:
                    for schema_name in schemas.keys():
                        print(f"    - {schema_name}")
        else:
            print("  No components section found in schema")
    
    # Configure logging level
    if debug_logging:
        logger.setLevel(logging.DEBUG)
    
    # Check if we should run serialization tests
    verbose = vmnf_handler.get('verbose', False)
    
    # New approach: Check for the dedicated serialization_test flag
    # This cleanly separates serialization tests from regular Pydantic tests
    serialization_test = vmnf_handler.get('serialization_test', False)
    
    # Legacy approach (for backward compatibility)
    test_type = vmnf_handler.get('pydantic_test_types', '')
    is_legacy_serialization = False
    if isinstance(test_type, str):
        is_legacy_serialization = test_type == 'serialization'
    elif isinstance(test_type, list):
        is_legacy_serialization = 'serialization' in test_type
    
    # Run serialization tests if either approach indicates we should
    if serialization_test or is_legacy_serialization:
        if verbose:
            if serialization_test:
                print("\n → Running serialization tests with --serialization-test flag")
            else:
                print("\n → Running serialization tests (legacy mode with --test-type serialization)")
        
        # Import serialization engine only when needed
        from .serialization_engine import run_serialization_tests
        
        # Run serialization tests in verbose mode for detailed output
        vmnf_handler['verbose'] = True  # Force verbose mode for serialization tests
        results = run_serialization_tests(vmnf_handler, schema)
        
        if results:
            if verbose:
                print(f" → Generated serialization tests for {len(results)} models")
            return results
        else:
            if verbose:
                print(" → No serialization test results generated")
    
    # Create tester
    tester = PydanticTester(**vmnf_handler)
    
    # Setup and run tests
    from ._async_compat import run_async
    results = run_async(tester.run_tests())
    
    if not results:
        if verbose:
            print("\n → No results from API testing, using schema-only testing mode...")
            
        # Import schema tester only when needed
        from .schema_tester import generate_schema_test_results
        
        # Generate test results directly from schema
        results = generate_schema_test_results(schema)
        
        if results:
            print(f" → Generated tests for {len(results)} models using schema-only mode")
    
    # With the new approach, serialization tests are completely separate from Pydantic tests
    # So we no longer need to add serialization tests to other test results
    # This section is only for backward compatibility
    
    # Check if we need to add serialization tests for backward compatibility
    is_legacy_case = False
    test_type = vmnf_handler.get('pydantic_test_types', '')
    
    if isinstance(test_type, str) and 'serialization' in test_type.split(',') and test_type != 'serialization':
        # Legacy case: Multiple test types including serialization
        is_legacy_case = True
    elif isinstance(test_type, list) and 'serialization' in test_type and len(test_type) > 1:
        # Legacy case: Multiple test types including serialization
        is_legacy_case = True
    
    if is_legacy_case and verbose:
        print("\n → WARNING: Using legacy mode with --pydantic-test --test-type including 'serialization'")
        print("   Consider using the new --serialization-test flag instead.")
    
    # Only run this for backward compatibility
    if is_legacy_case and not is_legacy_serialization:
        if verbose:
            print("\n → Adding serialization tests to results (legacy mode)")
        
        # Import serialization module
        from .serialization_engine import run_serialization_tests
        
        # Run serialization tests and merge with existing results
        serialization_results = run_serialization_tests(vmnf_handler, schema)
        
        if serialization_results:
            if verbose:
                print(f" → Added serialization tests for {len(serialization_results)} models")
            results.update(serialization_results)
    
    return results