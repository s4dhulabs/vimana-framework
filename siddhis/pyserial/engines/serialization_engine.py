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

import json
import yaml
import os
import logging
import random
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple, Type
from pydantic import BaseModel
from neotermcolor import colored

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("pyserial.serialization_engine")

# Helper functions for importing and launching the interactive builder
def import_interactive_builder():
    """Helper function to import the interactive payload builder with fallback mechanisms"""
    import sys
    import os
    import importlib.util

    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Parent directory of engines
    parent_dir = os.path.dirname(current_dir)

    # First try relative import
    try:
        from siddhis.pyserial.engines.payloads import launch_interactive_builder
        print("\n → Successfully imported interactive payload builder module")
        return launch_interactive_builder
    except ImportError:
        try:
            # Try direct import from parent
            sys.path.insert(0, parent_dir)
            from engines.payloads.interactive_payload_builder import launch_interactive_builder
            print("\n → Imported interactive payload builder using parent path")
            return launch_interactive_builder
        except ImportError:
            # Last resort - try direct import from current directory
            sys.path.insert(0, current_dir)
            from payloads.interactive_payload_builder import launch_interactive_builder
            print("\n → Imported interactive payload builder using fallback path")
            return launch_interactive_builder

def launch_interactive_builder_helper(test_data, vmnf_handler):
    """Helper function to launch the interactive payload builder with error handling"""
    try:
        # Import the interactive payload builder
        launch_fn = import_interactive_builder()

        # Check if we're in an interactive terminal
        import os
        import sys
        is_interactive_terminal = os.isatty(sys.stdout.fileno())

        # Configure vmnf_handler for interactive or non-interactive mode
        vmnf_handler = vmnf_handler.copy() if vmnf_handler else {}
        vmnf_handler["non_interactive"] = not is_interactive_terminal

        # Show notice about launching
        print("\n → Launching interactive payload builder...")
        if not is_interactive_terminal:
            print(" → Running in non-interactive mode because terminal isn't interactive")

        if "details" in test_data and "request" in test_data["details"]:
            url = test_data["details"]["request"].get("url", vmnf_handler.get("target_url", "unknown"))
        else:
            url = vmnf_handler.get("target_url", "unknown")

        print(" → Target URL: " + url)
        print(" → Test type: " + test_data.get('name', 'unknown'))
        if is_interactive_terminal:
            print(" → Press Ctrl+C to cancel if you want to skip the interactive mode")

        # Launch the interactive builder
        builder_result = launch_fn(test_data, vmnf_handler)

        mode = builder_result.get('mode', 'unknown')
        print("\n → Interactive builder finished: " + builder_result.get('status') + " (mode: " + mode + ")")
        if builder_result.get('status') == 'success':
            print(" → Log file: " + builder_result.get('log_file'))
            if 'payload_file' in builder_result:
                print(" → Payload file: " + builder_result.get('payload_file'))

        return builder_result

    except Exception as e:
        import traceback
        print("\n → Error launching interactive payload builder: " + str(e))
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

class SerializationTestVector:
    """
    Generates serialization test vectors for Pydantic models, focusing on edge cases
    and potential security vulnerabilities in serialization/deserialization.
    """

    def __init__(self, categories: Optional[List[str]] = None, custom_tests: Optional[Dict[str, Any]] = None):
        """
        Initialize the serialization test vector generator.

        Args:
            categories: Optional list of test categories to include
            custom_tests: Optional dictionary of custom tests loaded from a file
        """
        self.available_categories = [
            'depth_testing',
            'type_confusion',
            'binary_data',
            'circular_references',
            'large_nested_structures',
            'special_characters',
            'custom'
        ]

        # Store custom tests if provided
        self.custom_tests = custom_tests

        # Use all categories if none specified
        if categories:
            # Handle different types of input
            if isinstance(categories, str):
                # Convert comma-separated string to list
                cat_list = [cat.strip() for cat in categories.split(',')]
            else:
                cat_list = categories

            # Filter to ensure only valid categories are used
            self.categories = [cat for cat in cat_list if cat in self.available_categories]
            # If no valid categories remain, use all
            if not self.categories:
                self.categories = self.available_categories
        else:
            self.categories = self.available_categories

        # If custom tests are provided, always include the 'custom' category
        if self.custom_tests and 'custom' not in self.categories:
            self.categories.append('custom')

        logger.info(f"Initializing Serialization Test Vector with categories: {self.categories}")

    def generate_tests(self, model: Type[BaseModel]) -> List[Dict[str, Any]]:
        """
        Generate serialization tests for a given Pydantic model.

        Args:
            model: Pydantic model class to test

        Returns:
            List of test vectors
        """
        tests = []

        # Generate baseline test
        baseline_test = {
            "name": "serialization_baseline",
            "category": "baseline",
            "payload": self._generate_valid_data(model),
            "expected": "ACCEPTED"
        }
        tests.append(baseline_test)

        # Generate tests based on enabled categories
        if 'depth_testing' in self.categories:
            tests.extend(self._generate_depth_tests(model))

        if 'type_confusion' in self.categories:
            tests.extend(self._generate_type_confusion_tests(model))

        if 'binary_data' in self.categories:
            tests.extend(self._generate_binary_tests(model))

        if 'circular_references' in self.categories:
            tests.extend(self._generate_circular_tests(model))

        if 'large_nested_structures' in self.categories:
            tests.extend(self._generate_nested_structure_tests(model))

        if 'special_characters' in self.categories:
            tests.extend(self._generate_special_char_tests(model))

        if 'custom' in self.categories:
            tests.extend(self._generate_custom_tests(model))

        logger.info(f"Generated {len(tests)} serialization tests for model {model.__name__}")
        return tests

    def _generate_valid_data(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate valid data for a model to be used as baseline.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with valid data for the model
        """
        # Simple implementation that creates placeholder values based on field types
        data = {}
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        for field_name, field in model_fields.items():
            field_type = field.outer_type_

            # Generate appropriate value based on field type
            if field_type == str:
                data[field_name] = f"test_{field_name}"
            elif field_type == int:
                data[field_name] = 1
            elif field_type == float:
                data[field_name] = 1.0
            elif field_type == bool:
                data[field_name] = True
            elif field_type == list:
                data[field_name] = []
            elif field_type == dict:
                data[field_name] = {}
            else:
                # Try to provide a default value
                try:
                    default = field.get_default()
                    if default is not None:
                        data[field_name] = default
                    else:
                        data[field_name] = str(field_name)
                except:
                    data[field_name] = str(field_name)

        return data

    def _generate_depth_tests(self, model: Type[BaseModel]) -> List[Dict[str, Any]]:
        """
        Generate tests for recursive depth limits.

        Args:
            model: Pydantic model class

        Returns:
            List of test vectors targeting depth limits
        """
        tests = []

        # Recursive object with controllable depth
        tests.append({
            "name": "recursive_depth_small",
            "category": "depth_testing",
            "payload": self._generate_recursive_payload(model, depth=5),
            "expected": "ACCEPTED",
            "description": "Test with small recursive depth (5 levels)"
        })

        tests.append({
            "name": "recursive_depth_medium",
            "category": "depth_testing",
            "payload": self._generate_recursive_payload(model, depth=20),
            "expected": "SANITIZED",
            "description": "Test with medium recursive depth (20 levels)"
        })

        tests.append({
            "name": "recursive_depth_large",
            "category": "depth_testing",
            "payload": self._generate_recursive_payload(model, depth=100),
            "expected": "REJECTED",
            "description": "Test with large recursive depth (100 levels)"
        })

        return tests

    def _generate_recursive_payload(self, model: Type[BaseModel], depth: int = 10) -> Dict[str, Any]:
        """
        Generate a deeply nested recursive payload.

        Args:
            model: Pydantic model class
            depth: Recursive depth to generate

        Returns:
            Nested dictionary representing the payload
        """
        # Find a dict field to use for recursion, or use a default approach
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}
        dict_field = next((name for name, field in model_fields.items()
                          if field.outer_type_ == dict), None)

        # Generate baseline data
        base_data = self._generate_valid_data(model)

        # Create recursive structure
        if dict_field:
            current = base_data
            for i in range(depth):
                current[dict_field] = self._generate_valid_data(model)
                current = current[dict_field]
        else:
            # If no dict field is found, create a nested dict under a custom key
            current = base_data
            for i in range(depth):
                current["nested"] = {"level": i, "data": self._generate_valid_data(model)}
                current = current["nested"]

        return base_data

    def _generate_type_confusion_tests(self, model: Type[BaseModel]) -> List[Dict[str, Any]]:
        """
        Generate tests that attempt to confuse the serialization system with type issues.

        Args:
            model: Pydantic model class

        Returns:
            List of test vectors targeting type confusion
        """
        tests = []
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # JSON type confusion tests
        tests.append({
            "name": "type_confusion_numbers_as_strings",
            "category": "type_confusion",
            "payload": self._generate_typed_payload(model, int, str),
            "expected": "SANITIZED",
            "description": "Test with number fields converted to strings"
        })

        tests.append({
            "name": "type_confusion_booleans_as_numbers",
            "category": "type_confusion",
            "payload": self._generate_typed_payload(model, bool, int),
            "expected": "SANITIZED",
            "description": "Test with boolean fields converted to integers"
        })

        # String representation of objects
        tests.append({
            "name": "type_confusion_serialized_objects",
            "category": "type_confusion",
            "payload": self._generate_serialized_object_payload(model),
            "expected": "REJECTED",
            "description": "Test with serialized JSON strings instead of objects"
        })

        # Mixing arrays and objects
        tests.append({
            "name": "type_confusion_arrays_as_objects",
            "category": "type_confusion",
            "payload": self._generate_arrays_as_objects_payload(model),
            "expected": "REJECTED",
            "description": "Test with objects instead of arrays"
        })

        return tests

    def _generate_typed_payload(self, model: Type[BaseModel], target_type: Type,
                               conversion_type: Type) -> Dict[str, Any]:
        """
        Generate a payload with specific types converted to another type.

        Args:
            model: Pydantic model class
            target_type: Type to convert from
            conversion_type: Type to convert to

        Returns:
            Dictionary with converted values
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Find fields of target_type and convert them
        for field_name, field in model_fields.items():
            if field.outer_type_ == target_type and field_name in base_data:
                if conversion_type == str:
                    base_data[field_name] = str(base_data[field_name])
                elif conversion_type == int:
                    if target_type == bool:
                        base_data[field_name] = 1 if base_data[field_name] else 0
                    else:
                        try:
                            base_data[field_name] = int(base_data[field_name])
                        except:
                            base_data[field_name] = 0

        return base_data

    def _generate_serialized_object_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with serialized JSON strings instead of objects.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with serialized values
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Find dictionary or list fields and convert them to strings
        for field_name, field in model_fields.items():
            if field.outer_type_ in (dict, list) and field_name in base_data:
                # Create a sample complex object
                if field.outer_type_ == dict:
                    complex_obj = {"key1": "value1", "key2": 123, "nested": {"inner": "value"}}
                else:
                    complex_obj = [1, "two", {"three": 3}, [4, 5]]

                # Convert to string representation
                base_data[field_name] = json.dumps(complex_obj)

        return base_data

    def _generate_arrays_as_objects_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with objects instead of arrays.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with arrays converted to objects
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Find list fields and convert them to dictionaries
        for field_name, field in model_fields.items():
            if field.outer_type_ == list and field_name in base_data:
                # Convert list to dictionary with indices as keys
                base_data[field_name] = {"0": "item1", "1": "item2", "2": "item3"}

        return base_data

    def _generate_binary_tests(self, model: Type[BaseModel]) -> List[Dict[str, Any]]:
        """
        Generate tests with binary data.

        Args:
            model: Pydantic model class

        Returns:
            List of test vectors targeting binary data handling
        """
        tests = []

        # Test with Base64 encoded binary data in string fields
        tests.append({
            "name": "binary_data_base64",
            "category": "binary_data",
            "payload": self._generate_base64_payload(model),
            "expected": "ACCEPTED",
            "description": "Test with Base64 encoded binary data"
        })

        # Test with binary data encoded as Unicode escape sequences
        tests.append({
            "name": "binary_data_unicode_escapes",
            "category": "binary_data",
            "payload": self._generate_unicode_escape_payload(model),
            "expected": "ACCEPTED",
            "description": "Test with Unicode escape sequences"
        })

        # Test with null bytes in string fields
        tests.append({
            "name": "binary_data_null_bytes",
            "category": "binary_data",
            "payload": self._generate_null_byte_payload(model),
            "expected": "SANITIZED",
            "description": "Test with null bytes in string fields"
        })

        return tests

    def _generate_base64_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with Base64 encoded binary data.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with Base64 data in string fields
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Sample Base64 strings
        base64_samples = [
            "SGVsbG8gV29ybGQ=",  # "Hello World"
            "VGVzdGluZyBCaW5hcnkgRGF0YQ==",  # "Testing Binary Data"
            "U2VyaWFsaXphdGlvbiBWdWxuZXJhYmlsaXR5",  # "Serialization Vulnerability"
        ]

        # Put Base64 data in string fields
        for field_name, field in model_fields.items():
            if field.outer_type_ == str and field_name in base_data:
                base_data[field_name] = random.choice(base64_samples)

        return base_data

    def _generate_unicode_escape_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with Unicode escape sequences.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with Unicode escape sequences in string fields
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Sample Unicode escape sequences
        unicode_samples = [
            "\\u0000\\u0001\\u0002\\u0003",  # Control characters
            "Test\\u2022ing",  # Bullet point
            "\\uD83D\\uDE00",  # Emoji (😀)
        ]

        # Put Unicode escapes in string fields
        for field_name, field in model_fields.items():
            if field.outer_type_ == str and field_name in base_data:
                base_data[field_name] = random.choice(unicode_samples)

        return base_data

    def _generate_null_byte_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with null bytes in string fields.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with null bytes in string fields
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Put null bytes in string fields
        for field_name, field in model_fields.items():
            if field.outer_type_ == str and field_name in base_data:
                base_data[field_name] = f"Before\0After"

        return base_data

    def _generate_circular_tests(self, model: Type[BaseModel]) -> List[Dict[str, Any]]:
        """
        Generate tests with circular references.

        Args:
            model: Pydantic model class

        Returns:
            List of test vectors targeting circular reference handling
        """
        tests = []

        # Simple circular reference
        tests.append({
            "name": "circular_reference_direct",
            "category": "circular_references",
            "payload": self._generate_direct_circular_payload(model),
            "expected": "REJECTED",
            "description": "Test with direct circular reference"
        })

        # Delayed circular reference
        tests.append({
            "name": "circular_reference_indirect",
            "category": "circular_references",
            "payload": self._generate_indirect_circular_payload(model),
            "expected": "REJECTED",
            "description": "Test with indirect circular reference"
        })

        # Invalid JSON representation
        tests.append({
            "name": "circular_reference_representation",
            "category": "circular_references",
            "payload": self._generate_circular_representation_payload(model),
            "expected": "REJECTED",
            "description": "Test with circular reference JSON representation"
        })

        return tests

    def _generate_direct_circular_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with a direct circular reference.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with circular reference
        """
        base_data = self._generate_valid_data(model)

        # Create a circular reference
        # Note: This will actually be handled by JSON when serializing
        base_data["self_reference"] = base_data

        return base_data

    def _generate_indirect_circular_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with an indirect circular reference.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with indirect circular reference
        """
        base_data = self._generate_valid_data(model)

        # Create an indirect circular reference
        base_data["level1"] = {"level2": {"level3": {}}}
        base_data["level1"]["level2"]["level3"]["back_to_level1"] = base_data["level1"]

        return base_data

    def _generate_circular_representation_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload that hints at a circular reference.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with circular reference representation
        """
        base_data = self._generate_valid_data(model)

        # Use string representations that could confuse parsers
        base_data["circular_json"] = '"{"circular": ${circular_json}}"'

        return base_data

    def _generate_nested_structure_tests(self, model: Type[BaseModel]) -> List[Dict[str, Any]]:
        """
        Generate tests with large nested structures.

        Args:
            model: Pydantic model class

        Returns:
            List of test vectors targeting nested structure handling
        """
        tests = []

        # Test with deeply nested arrays
        tests.append({
            "name": "nested_structure_arrays",
            "category": "large_nested_structures",
            "payload": self._generate_nested_arrays_payload(model),
            "expected": "SANITIZED",
            "description": "Test with deeply nested arrays"
        })

        # Test with deeply nested objects
        tests.append({
            "name": "nested_structure_objects",
            "category": "large_nested_structures",
            "payload": self._generate_nested_objects_payload(model),
            "expected": "SANITIZED",
            "description": "Test with deeply nested objects"
        })

        # Test with a large number of properties
        tests.append({
            "name": "nested_structure_many_properties",
            "category": "large_nested_structures",
            "payload": self._generate_many_properties_payload(model),
            "expected": "SANITIZED",
            "description": "Test with a large number of properties"
        })

        return tests

    def _generate_nested_arrays_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with deeply nested arrays.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with deeply nested arrays
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Find the first list field
        list_field = next((name for name, field in model_fields.items()
                          if field.outer_type_ == list), None)

        if list_field and list_field in base_data:
            # Create a deeply nested array structure
            nested_array = "item"
            for i in range(20):  # 20 levels of nesting
                nested_array = [nested_array]

            base_data[list_field] = nested_array
        else:
            # If no list field exists, add a custom one
            base_data["nested_arrays"] = []
            current = base_data["nested_arrays"]

            for i in range(20):  # 20 levels of nesting
                current.append([])
                current = current[0]

            current.append("Deeply nested item")

        return base_data

    def _generate_nested_objects_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with deeply nested objects.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with deeply nested objects
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Find the first dict field
        dict_field = next((name for name, field in model_fields.items()
                          if field.outer_type_ == dict), None)

        if dict_field and dict_field in base_data:
            # Create a deeply nested object structure
            nested_obj = {"value": "Deeply nested value"}
            for i in range(20):  # 20 levels of nesting
                nested_obj = {"nested": nested_obj}

            base_data[dict_field] = nested_obj
        else:
            # If no dict field exists, add a custom one
            current = base_data

            for i in range(20):  # 20 levels of nesting
                current["nested_object"] = {}
                current = current["nested_object"]

            current["value"] = "Deeply nested value"

        return base_data

    def _generate_many_properties_payload(self, model: Type[BaseModel], size: int = 500) -> Dict[str, Any]:
        """
        Generate a payload with a large number of properties.

        Args:
            model: Pydantic model class
            size: Number of properties to generate (default: 500)

        Returns:
            Dictionary with many properties
        """
        base_data = self._generate_valid_data(model)

        # Add many properties to the base data
        for i in range(size):
            base_data[f"property_{i}"] = f"value_{i}"

        return base_data

    def _generate_special_char_tests(self, model: Type[BaseModel]) -> List[Dict[str, Any]]:
        """
        Generate tests with special characters.

        Args:
            model: Pydantic model class

        Returns:
            List of test vectors targeting special character handling
        """
        tests = []

        # Test with Unicode special characters
        tests.append({
            "name": "special_chars_unicode",
            "category": "special_characters",
            "payload": self._generate_unicode_payload(model),
            "expected": "ACCEPTED",
            "description": "Test with Unicode special characters"
        })

        # Test with control characters
        tests.append({
            "name": "special_chars_control",
            "category": "special_characters",
            "payload": self._generate_control_chars_payload(model),
            "expected": "SANITIZED",
            "description": "Test with control characters"
        })

        # Test with quote escaping
        tests.append({
            "name": "special_chars_quotes",
            "category": "special_characters",
            "payload": self._generate_quote_escaping_payload(model),
            "expected": "ACCEPTED",
            "description": "Test with quote characters that need escaping"
        })

        return tests

    def _generate_unicode_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with Unicode special characters.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with Unicode characters in string fields
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Sample Unicode characters
        unicode_samples = [
            "𝓗𝓮𝓵𝓵𝓸 𝓦𝓸𝓻𝓵𝓭",  # Script letters
            "你好，世界",  # Chinese
            "👨‍👩‍👧‍👦🚀🌍",  # Emoji
            "Ñandú åéîøü",  # Latin with diacritics
        ]

        # Put Unicode in string fields
        for field_name, field in model_fields.items():
            if field.outer_type_ == str and field_name in base_data:
                base_data[field_name] = random.choice(unicode_samples)

        return base_data

    def _generate_control_chars_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with control characters.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with control characters in string fields
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Control characters collection
        control_chars = "".join(chr(i) for i in range(32))

        # Put control characters in string fields
        for field_name, field in model_fields.items():
            if field.outer_type_ == str and field_name in base_data:
                # Mix regular text with control characters
                base_data[field_name] = f"Before{control_chars}After"

        return base_data

    def _generate_quote_escaping_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with quotes that need escaping.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with quote characters in string fields
        """
        base_data = self._generate_valid_data(model)
        model_fields = model.__fields__ if hasattr(model, '__fields__') else {}

        # Sample strings with quotes
        quote_samples = [
            'Single quotes \' inside a string',
            "Double quotes \" inside a string",
            'Mixed quotes " and \' inside a string',
            "Nested \"quotes\" within \"multiple \"levels\" of\" quotes",
        ]

        # Put quotes in string fields
        for field_name, field in model_fields.items():
            if field.outer_type_ == str and field_name in base_data:
                base_data[field_name] = random.choice(quote_samples)

        return base_data

    def _generate_custom_tests(self, model: Type[BaseModel]) -> List[Dict[str, Any]]:
        """
        Generate custom tests based on model-specific properties or loaded custom tests.

        Args:
            model: Pydantic model class

        Returns:
            List of test vectors with custom tests
        """
        tests = []

        # Process custom tests loaded from file if available
        if self.custom_tests:
            if isinstance(self.custom_tests, list):
                # Custom tests provided as a list of test definitions
                for test_def in self.custom_tests:
                    test = {
                        "name": test_def.get("name", f"custom_test_{len(tests)}"),
                        "category": "custom",
                        "expected": test_def.get("expected", "REJECTED"),
                        "description": test_def.get("description", "Custom serialization test"),
                        # Include source file if present in the original test definition
                        "source_file": test_def.get("source_file", "")
                    }

                    # Handle payload based on type
                    payload_def = test_def.get("payload", {})
                    if isinstance(payload_def, dict):
                        # Use payload directly
                        test["payload"] = payload_def
                    elif isinstance(payload_def, str) and payload_def == "BASE_MODEL":
                        # Generate a base model and apply transformations
                        base_data = self._generate_valid_data(model)
                        transformations = test_def.get("transformations", [])

                        for transform in transformations:
                            transform_type = transform.get("type")
                            if transform_type == "add_field":
                                field = transform.get("field")
                                value = transform.get("value")
                                if field and value is not None:
                                    base_data[field] = value
                            elif transform_type == "modify_field":
                                field = transform.get("field")
                                value = transform.get("value")
                                if field in base_data and value is not None:
                                    base_data[field] = value
                            elif transform_type == "nest":
                                depth = transform.get("depth", 5)
                                field = transform.get("field", "nested")
                                current = base_data
                                for i in range(depth):
                                    current[field] = {}
                                    current = current[field]
                                current["value"] = transform.get("value", "Deeply nested value")

                        test["payload"] = base_data

                    tests.append(test)
            elif isinstance(self.custom_tests, dict):
                # Custom tests provided as a dictionary with test configurations
                config = self.custom_tests.get("config", {})
                test_defs = self.custom_tests.get("tests", [])

                for test_def in test_defs:
                    # Apply global config with test-specific overrides
                    test_name = test_def.get("name", f"custom_test_{len(tests)}")
                    test_category = test_def.get("category", config.get("category", "custom"))
                    test_expected = test_def.get("expected", config.get("expected", "REJECTED"))
                    test_desc = test_def.get("description", config.get("description", "Custom serialization test"))

                    # Create test with payload
                    test = {
                        "name": test_name,
                        "category": test_category,
                        "expected": test_expected,
                        "description": test_desc,
                        # Include source file if present in the original test definition
                        "source_file": test_def.get("source_file", "")
                    }

                    # Generate payload based on config
                    if "payload" in test_def:
                        test["payload"] = test_def["payload"]
                    elif "payload_type" in test_def:
                        payload_type = test_def["payload_type"]

                        if payload_type == "recursive":
                            depth = test_def.get("depth", config.get("depth", 10))
                            test["payload"] = self._generate_recursive_payload(model, depth)
                        elif payload_type == "circular":
                            test["payload"] = self._generate_direct_circular_payload(model)
                        elif payload_type == "binary":
                            test["payload"] = self._generate_base64_payload(model)
                        elif payload_type == "large":
                            size = test_def.get("size", config.get("size", 1000))
                            test["payload"] = self._generate_many_properties_payload(model, size)
                        elif payload_type == "special_chars":
                            test["payload"] = self._generate_unicode_payload(model)
                        else:
                            # Default to valid data
                            test["payload"] = self._generate_valid_data(model)
                    else:
                        test["payload"] = self._generate_valid_data(model)

                    tests.append(test)

        # Add default custom tests if no custom tests are provided or if there are none
        if not tests:
            tests.append({
                "name": "custom_serialization_json_patch",
                "category": "custom",
                "payload": self._generate_json_patch_payload(model),
                "expected": "REJECTED",
                "description": "Test with JSON Patch-like structure that might be misinterpreted"
            })

            tests.append({
                "name": "custom_serialization_json_pointer",
                "category": "custom",
                "payload": self._generate_json_pointer_payload(model),
                "expected": "SANITIZED",
                "description": "Test with JSON Pointer references"
            })

        return tests

    def _generate_json_patch_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload that resembles a JSON Patch document.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with JSON Patch operations
        """
        base_data = self._generate_valid_data(model)

        # Add JSON Patch-like operations
        base_data["operations"] = [
            {"op": "replace", "path": "/sensitive_field", "value": "hacked_value"},
            {"op": "remove", "path": "/security_check"},
            {"op": "add", "path": "/admin", "value": True},
        ]

        return base_data

    def _generate_json_pointer_payload(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """
        Generate a payload with JSON Pointer references.

        Args:
            model: Pydantic model class

        Returns:
            Dictionary with JSON Pointer references
        """
        base_data = self._generate_valid_data(model)

        # Add JSON Pointer references
        base_data["pointers"] = {
            "ref1": "#/field1",
            "ref2": "#/nested/field2",
            "external": "https://example.com/schema#/properties/field",
        }

        return base_data

def run_serialization_tests(vmnf_handler: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point function for running serialization tests from PySerial.

    Args:
        vmnf_handler: Vimana framework handler
        schema: API schema to test

    Returns:
        Dictionary of test results
    """
    logger.info("Starting serialization tests")

    # Always enable verbose mode for better user experience with serialization tests
    vmnf_handler['verbose'] = True
    verbose = True

    # If using custom payload builder, ensure we create detailed test logs
    set_custom_payload = vmnf_handler.get('set_custom_payload', False)
    if set_custom_payload:
        logger.info("Interactive payload builder enabled - detailed test logs will be generated")

    # Ensure the serialization_test flag is set in the handler
    vmnf_handler['serialization_test'] = True

    # Get serialization categories from test_type (new approach) or test_categories (legacy)
    # This provides backward compatibility with both approaches
    serialization_test = vmnf_handler.get('serialization_test', True)
    serialization_categories = None

    # For backward compatibility, get the legacy test_type (used in check below)
    test_type = vmnf_handler.get('pydantic_test_types', '')

    # New approach: Using --serialization-test with --test-type for categories
    serialization_categories = vmnf_handler.get('test_type', '')

    # If no categories specified, fall back to test_categories (legacy approach)
    if not serialization_categories:
        serialization_categories = vmnf_handler.get('test_categories', '')

    # Debug logging for input parameters
    if verbose:
        print(f"\n → Serialization test parameters:")
        print(f"   - Serialization test enabled: {serialization_test}")
        print(f"   - Serialization categories: {serialization_categories}")
        print(f"   - Models: {vmnf_handler.get('pydantic_models')}")

    # Parse serialization categories
    if serialization_categories:
        if isinstance(serialization_categories, str):
            # Handle comma-separated string
            categories = [cat.strip() for cat in serialization_categories.split(',')]
        elif isinstance(serialization_categories, list):
            # Already a list
            categories = serialization_categories
        else:
            # Default to all categories
            categories = None
    else:
        # Default to all categories
        categories = None

    # Make sure the categories actually match what we support
    valid_categories = ["depth_testing", "type_confusion", "binary_data",
                       "circular_references", "large_nested_structures",
                       "special_characters", "custom"]

    if categories:
        # Filter to only include valid categories
        categories = [cat for cat in categories if cat in valid_categories]
        # If none remain valid, use all
        if not categories:
            categories = valid_categories
            if verbose:
                print(f" → No valid categories specified, using all categories")
        else:
            if verbose:
                print(f" → Using categories: {', '.join(categories)}")
    else:
        categories = valid_categories
        if verbose:
            print(f" → Using all serialization test categories")

    logger.info(f"Serialization test categories: {categories}")

    # In the new approach with --serialization-test flag, we skip this check because
    # we're explicitly running serialization tests through a dedicated flag and path
    # This check is only relevant for the legacy approach
    if not serialization_test and test_type:
        # Handle both string and list test types
        if isinstance(test_type, str):
            is_serialization = test_type == 'serialization'
        elif isinstance(test_type, list):
            is_serialization = 'serialization' in test_type
        else:
            is_serialization = False

        if not is_serialization:
            logger.info(f"Test type is {test_type}, not running serialization tests")
            return {}

    # Check if a custom test path is provided
    custom_test_path = vmnf_handler.get('custom_test', '')
    custom_tests = None
    using_custom_test_file = False
    custom_test_files = []

    if custom_test_path and os.path.exists(custom_test_path):
        # Check if it's a directory or a file
        if os.path.isdir(custom_test_path):
            # It's a directory, find all YAML/JSON files
            print(f"\n{colored('━━━ CUSTOM SERIALIZATION TEST DIRECTORY ━━━', 'cyan', attrs=['bold'])}")
            print(f"Scanning directory: {colored(custom_test_path, 'green')}")
            print(f"{'━' * 50}")

            # Get all yaml/yml/json files in the directory
            all_files = os.listdir(custom_test_path)
            yaml_files = [f for f in all_files if f.endswith(('.yaml', '.yml', '.json'))]

            if not yaml_files:
                print(f" → {colored('No test files found', 'red')} in {custom_test_path}")
                print(f" → Looking for files with extensions: .yaml, .yml, .json")
            else:
                print(f" → Found {colored(len(yaml_files), 'green')} test files:")
                for i, file in enumerate(yaml_files, 1):
                    print(f"    {i}. {colored(file, 'yellow')}")

                # Store full paths to process later
                custom_test_files = [os.path.join(custom_test_path, f) for f in yaml_files]
                using_custom_test_file = True

                print(f"\n{colored('Loading all test files...', 'cyan')}")

        else:
            # It's a single file
            custom_test_files = [custom_test_path]
            using_custom_test_file = True

        # Process all test files
        if custom_test_files:
            # Prepare to merge all custom tests
            merged_custom_tests = {
                "config": {
                    "description": "Merged custom serialization tests"
                },
                "tests": []
            }

            # Process each file
            for test_file in custom_test_files:
                try:
                    file_tests = None

                    # Load tests based on file extension
                    if test_file.endswith(('.yaml', '.yml')):
                        with open(test_file, 'r') as f:
                            file_tests = yaml.safe_load(f)
                    elif test_file.endswith('.json'):
                        with open(test_file, 'r') as f:
                            file_tests = json.load(f)
                    else:
                        print(f" → {colored('Skipping unsupported file format', 'yellow')}: {test_file}")
                        print(f"    Supported formats: .yaml, .yml, .json")
                        continue

                    # Add file info to the tests for better tracking
                    filename = os.path.basename(test_file)

                    # Print test file details
                    print(f"\n{colored('━━━ TEST FILE ━━━', 'cyan')}")
                    print(f" → Loading: {colored(filename, 'yellow')}")

                    # Extract and show test configuration
                    if isinstance(file_tests, dict):
                        # Get test config
                        config = file_tests.get('config', {})
                        description = config.get('description', 'No description')
                        test_count = len(file_tests.get('tests', []))

                        # Update merged tests config if this is the first file with a description
                        if description != 'No description' and merged_custom_tests['config']['description'] == 'Merged custom serialization tests':
                            merged_custom_tests['config']['description'] = description

                        # Show test file summary
                        print(f" → Description: {colored(description, 'green')}")
                        print(f" → Test count: {colored(test_count, 'green')} tests")

                        # Display test names and descriptions
                        if test_count > 0:
                            print(f"\n Test vectors in {colored(filename, 'yellow')}:")
                            for i, test in enumerate(file_tests.get('tests', []), 1):
                                name = test.get('name', f'Test #{i}')
                                desc = test.get('description', 'No description')
                                expected = test.get('expected', 'UNKNOWN')

                                # Add file info to each test
                                test['source_file'] = filename

                                # Add to merged tests
                                merged_custom_tests['tests'].append(test)

                                # Display test info
                                print(f"  {i}. {colored(name, 'yellow')} - {desc}")
                                print(f"     Expected: {colored(expected, 'blue')}")
                    else:
                        print(f" → {colored('Warning', 'yellow')}: File format not recognized, skipping.")

                except Exception as e:
                    logger.error(f"Error loading custom test file {test_file}: {str(e)}")
                    print(f" → {colored('Error loading custom test file', 'red')}: {test_file}")
                    print(f"   {str(e)}")

            # Set the merged custom tests as our test data
            custom_tests = merged_custom_tests

            # Show summary of all loaded tests
            total_tests = len(merged_custom_tests.get('tests', []))
            if total_tests > 0:
                print(f"\n{colored('━━━ TESTING SUMMARY ━━━', 'cyan')}")
                print(f" → Total custom tests loaded: {colored(total_tests, 'green')}")
                print(f" → From {colored(len(custom_test_files), 'green')} test files")
                print(f"{'━' * 50}")
            else:
                print(f"\n{colored('No tests found in the specified files.', 'red')}")
                print(f"Please check your test files for valid test definitions.")
    else:
        if custom_test_path:
            print(f"{colored('Error:', 'red')} Custom test path not found: {custom_test_path}")

    # When using custom tests, only run custom tests (not the standard categories)
    if using_custom_test_file:
        # Set categories to only 'custom' when using custom test files
        categories = ['custom']

    # Create serialization test vector generator
    test_vector_generator = SerializationTestVector(categories, custom_tests=custom_tests)

    # Placeholder for importing and testing Pydantic models from schema
    # In a real implementation, this would extract models from the schema
    # and create actual test instances for each

    # Extract schema components
    components = schema.get('components', {})
    schemas = components.get('schemas', {})

    # Check if a target URL is provided
    target_url = vmnf_handler.get('target_url', '').rstrip('/')
    if not target_url:
        logger.warning("No target URL provided for serialization tests")
        return {
            "SerializationTests": {
                "model_name": "SerializationTests",
                "fields": {
                    "serialization_field": [
                        {
                            "name": "No target URL",
                            "test_type": "serialization",
                            "description": "No target URL provided for serialization tests",
                            "expected_result": "TARGET_REQUIRED",
                            "actual_result": "WARNING",
                            "status_code": None,
                            "pass": False
                        }
                    ]
                }
            }
        }

    # If no schemas found, return placeholder
    if not schemas:
        logger.warning("No schemas found in the OpenAPI specification")
        results = {
            "SerializationTests": {
                "model_name": "SerializationTests",
                "fields": {
                    "serialization_field": [
                        {
                            "name": "No schemas found",
                            "test_type": "serialization",
                            "description": "No schemas were found in the OpenAPI specification",
                            "expected_result": "NO_SCHEMAS_FOUND",
                            "actual_result": "WARNING",
                            "status_code": None,
                            "pass": False
                        }
                    ]
                }
            }
        }
        return results

    # Create results for each schema
    results = {}

    # Import httpx for making HTTP requests
    import httpx
    import asyncio
    import json
    from datetime import datetime

    # Create a function to perform actual serialization tests against the API
    async def perform_serialization_tests(target_url):
        # Use the outer verbose variable
        nonlocal verbose
        colors_disabled = vmnf_handler.get('colors_disabled', False)
        all_test_results = {}

        # Create a display handler for interactive output
        display = SerializationTestDisplay(colors_disabled=colors_disabled)

        # Set up HTTP client
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            # First get available tests endpoint (if it exists)
            try:
                if verbose:
                    print(f" → Checking for serialization test endpoints on {target_url}")

                # Attempt to get serialization test info
                test_info_url = f"{target_url}/serialization-tests"
                test_info_response = await client.get(test_info_url)

                if test_info_response.status_code == 200:
                    test_info = test_info_response.json()
                    is_serialization_api = True
                    if verbose:
                        print(f" → Found serialization test API with {len(test_info.get('available_tests', []))} test endpoints")
                else:
                    is_serialization_api = False
                    if verbose:
                        print(f" → Target does not appear to be a serialization test API ({test_info_response.status_code})")
                print()
            except Exception as e:
                is_serialization_api = False
                if verbose:
                    print(f" → Error checking for serialization test endpoints: {str(e)}")

            # Map test categories to API endpoints
            # The serialization lab has specific endpoints for each category
            category_endpoints = {
                "circular_references": "/circular-reference/create",
                "depth_testing": "/nested-structure/create",
                "binary_data": "/binary-data/process",
                "type_confusion": "/type-confusion/process",
                "large_nested_structures": "/large-structure/create",
                "special_characters": "/special-characters/process",
                "custom": "/custom-serialization/process"
            }

            # Generate test vectors for schemas found in the API
            test_categories = test_vector_generator.categories
            max_schemas = 5  # Limit the number of schemas to test

            # Check if we have custom tests from files that should be run directly
            custom_tests_to_run = []
            if custom_tests and isinstance(custom_tests, dict) and "tests" in custom_tests:
                # Store references to custom tests for later execution
                custom_tests_to_run = custom_tests["tests"]
                if verbose:
                    print(f" → Found {len(custom_tests_to_run)} custom tests to execute directly")

            # Extract schemas for testing
            sample_schemas = list(schemas.items())[:max_schemas]

            for schema_name, schema_def in sample_schemas:
                # Create a test model result entry
                tests_for_model = []

                # First add any direct custom tests if we're in the first schema
                # This ensures we run the tests at least once
                if schema_name == sample_schemas[0][0] and custom_tests_to_run:
                    # Process custom tests for the first model
                    for test_def in custom_tests_to_run:
                        test_name = test_def.get("name", "custom_test")
                        test_desc = test_def.get("description", "Custom serialization test")
                        test_category = test_def.get("category", "custom")
                        test_expected = test_def.get("expected", "REJECTED")
                        source_file = test_def.get("source_file", "")

                        # Create test result structure
                        custom_test = {
                            "name": test_name,
                            "test_type": "serialization",
                            "category": test_category,
                            "description": test_desc,
                            "expected_result": test_expected,
                            "actual_result": "UNDETERMINED",
                            "status_code": None,
                            "pass": False,
                            "source_file": source_file,
                            "details": {}
                        }

                        # Extract payload
                        payload = test_def.get("payload", {})

                        # Determine appropriate endpoint based on category
                        endpoint_category = test_category.lower()
                        test_endpoint = category_endpoints.get(endpoint_category, category_endpoints.get("custom"))

                        # Special case for pickle tests - route them to binary_data endpoint
                        if isinstance(payload, dict) and payload.get("data_type") == "pickle":
                            test_endpoint = category_endpoints.get("binary_data")

                            # Add debug info about the pickle payload
                            if verbose:
                                data = payload.get("data", "")
                                if data:
                                    data_len = len(data)
                                    custom_test["details"]["debug"] = {
                                        "data_type": "pickle",
                                        "data_length": data_len,
                                        "data_padding": data[-1] if data else "",
                                        "payload_keys": list(payload.keys())
                                    }

                            # Validate base64 encoding - fix padding if needed
                            data = payload.get("data", "")
                            if data:
                                # Ensure proper base64 padding
                                missing_padding = len(data) % 4
                                if missing_padding:
                                    data += "=" * (4 - missing_padding)
                                    payload["data"] = data

                        # Construct URL and prepare request
                        test_url = f"{target_url}{test_endpoint}"

                        # Execute the test
                        try:
                            # Prepare request details for display
                            request_details = {
                                "url": test_url,
                                "method": "POST",
                                "body": payload
                            }
                            custom_test["details"]["request"] = request_details

                            # Make the request
                            response = await client.post(test_url, json=payload)

                            # Process response
                            if response:
                                custom_test["status_code"] = response.status_code

                                # Try to parse response
                                try:
                                    response_data = response.json()
                                    custom_test["details"]["response"] = response_data

                                    # Only save detailed test information to log files if debug is enabled
                                    debug_enabled = vmnf_handler.get('debug', False)
                                    if debug_enabled:
                                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        test_log_file = f"test_details_{timestamp}.log"
                                        with open(test_log_file, 'w') as f:
                                            json.dump({
                                                "test_name": custom_test.get("name", "Unknown Test"),
                                                "request": custom_test["details"].get("request", {}),
                                                "response": response_data,
                                                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            }, f, indent=2)

                                        # Print information about the test log file
                                        print(f" → Test details saved to: {test_log_file}")

                                    # Analyze response to determine result
                                    if response.status_code < 400:
                                        # Check for execution result from pickle tests
                                        if isinstance(payload, dict) and payload.get("data_type") == "pickle":
                                            # Mark as a vulnerability in several scenarios:
                                            # 1. If there's a 'deserialized' field in the response
                                            # 2. If the payload had 'data_type': 'pickle' (all pickle deserialization is dangerous)
                                            if "deserialized" in response_data or (
                                                isinstance(payload, dict) and
                                                payload.get("data_type") == "pickle" and
                                                response.status_code < 400
                                            ):
                                                custom_test["actual_result"] = "VULNERABILITY_FOUND"
                                                custom_test["vulnerability_details"] = {
                                                    "type": "pickle_deserialization",
                                                    "payload": payload,
                                                    "response": response_data
                                                }
                                            else:
                                                custom_test["actual_result"] = "ACCEPTED"
                                        else:
                                            # Standard successful response
                                            custom_test["actual_result"] = "ACCEPTED"
                                    else:
                                        # Error response
                                        custom_test["actual_result"] = "REJECTED"

                                except Exception as e:
                                    custom_test["actual_result"] = f"RESPONSE_PARSE_ERROR: {str(e)}"
                            else:
                                custom_test["actual_result"] = "NO_RESPONSE"

                            # Determine if test passed based on expectations
                            actual = custom_test["actual_result"]
                            expected = custom_test["expected_result"]

                            # Logic for determining if test passed
                            if expected == "REJECTED" and actual == "REJECTED":
                                custom_test["pass"] = True
                            elif expected == "ACCEPTED" and actual == "ACCEPTED":
                                custom_test["pass"] = True
                            elif expected == "SANITIZED" and actual in ["ACCEPTED", "SANITIZED"]:
                                custom_test["pass"] = True
                            elif expected == "VULNERABILITY_FOUND" and actual == "VULNERABILITY_FOUND":
                                custom_test["pass"] = True

                            # Special case for pickle tests - always consider successful pickle deserialization a vulnerability
                            # This is the key for the minimal_pickle_rce.yaml test
                            pickle_success = (
                                isinstance(payload, dict) and
                                payload.get("data_type") == "pickle" and
                                response.status_code < 400
                            )

                            # For pickle tests, consider a successful deserialization as a found vulnerability
                            # regardless of the expected result
                            if pickle_success:
                                custom_test["actual_result"] = "VULNERABILITY_FOUND"
                                if "vulnerability_details" not in custom_test:
                                    custom_test["vulnerability_details"] = {
                                        "type": "pickle_deserialization",
                                        "payload": payload,
                                        "response": response_data
                                    }

                                # Check if custom payload generation is requested
                                set_custom_payload = vmnf_handler.get('set_custom_payload', False)
                                if set_custom_payload:
                                    # Create log directory if it doesn't exist
                                    os.makedirs("custom_payloads", exist_ok=True)

                                    # Save detailed test information to log file
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    log_file = f"custom_payloads/vulnerability_{timestamp}.log"
                                    # Also save to lasttest.log for compatibility

                                    # Prepare vulnerability details properly
                                    vuln_details = {
                                        "type": "pickle_deserialization",
                                        "payload": payload,  # Use actual payload directly
                                        "response": response_data,  # Use actual response data
                                        "test_name": custom_test.get("name", "pickle_test")
                                    }
                                    custom_test["vulnerability_details"] = vuln_details

                                    # Save to the standard lasttest.log file
                                    with open("lasttest.log", 'w') as f:
                                        json.dump({
                                            "test": custom_test,
                                            "vulnerability_details": vuln_details,
                                            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        }, f, indent=2)

                                    # Save to the timestamped file too
                                    with open(log_file, 'w') as f:
                                        json.dump({
                                            "test": custom_test,
                                            "vulnerability_details": vuln_details,
                                            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        }, f, indent=2)

                                    print(f"\n → Test details saved to: {log_file}")

                                    # Launch the interactive payload builder
                                    print(f"\n → Vulnerability found! Launching interactive payload builder...")

                                    try:
                                        # Use our helper function to launch interactive builder
                                        launch_interactive_builder_helper(custom_test, vmnf_handler)

                                        # Add test to results and return early to stop testing
                                        tests_for_model.append(custom_test)
                                        all_test_results[schema_name] = {
                                            "model_name": schema_name,
                                            "fields": {
                                                "serialization_tests": tests_for_model
                                            }
                                        }
                                        return all_test_results
                                    except Exception as e:
                                        print(f"\n → Error launching interactive payload builder: {str(e)}")

                        except Exception as e:
                            custom_test["actual_result"] = f"TEST_ERROR: {str(e)}"

                        # Add the custom test to the results
                        tests_for_model.append(custom_test)

                # Then run regular category tests
                for category in test_categories:
                    # Base test result structure
                    test_result = {
                        "name": f"serialization_{category}",
                        "test_type": "serialization",
                        "category": category,
                        "description": f"Serialization tests for {category} category",
                        "expected_result": "VULNERABILITY_POSSIBLE",
                        "actual_result": "UNDETERMINED",
                        "status_code": None,
                        "pass": True,
                        "details": {}
                    }

                    # If we confirmed this is a serialization test API, perform actual tests
                    if is_serialization_api:
                        endpoint = category_endpoints.get(category, "")
                        if endpoint:
                            try:
                                # Create a placeholder for request details to show in output
                                request_details = {}

                                # Create an appropriate test payload based on the category
                                if category == "circular_references":
                                    test_url = f"{target_url}{endpoint}?depth=5"
                                    request_details = {
                                        "url": test_url,
                                        "method": "POST",
                                        "params": {"depth": 5}
                                    }
                                    response = await client.post(test_url)
                                elif category == "depth_testing":
                                    test_url = f"{target_url}{endpoint}?depth=100"
                                    request_details = {
                                        "url": test_url,
                                        "method": "POST",
                                        "params": {"depth": 100}
                                    }
                                    response = await client.post(test_url)
                                elif category == "binary_data":
                                    # Get sample pickle data
                                    pickle_url = f"{target_url}/binary-data/create-pickle-sample"
                                    pickle_response = await client.get(pickle_url)
                                    if pickle_response.status_code == 200:
                                        pickle_data = pickle_response.json()
                                        # Submit the pickle data
                                        test_url = f"{target_url}{endpoint}"
                                        request_details = {
                                            "url": test_url,
                                            "method": "POST",
                                            "body": pickle_data
                                        }
                                        response = await client.post(
                                            test_url,
                                            json=pickle_data
                                        )
                                    else:
                                        response = None
                                elif category == "type_confusion":
                                    # Get sample payload
                                    example_url = f"{target_url}/type-confusion/example"
                                    example_response = await client.get(example_url)
                                    if example_response.status_code == 200:
                                        examples = example_response.json()
                                        invalid_example = examples.get("invalid_example", {})
                                        test_url = f"{target_url}{endpoint}"
                                        request_details = {
                                            "url": test_url,
                                            "method": "POST",
                                            "body": invalid_example
                                        }
                                        response = await client.post(
                                            test_url,
                                            json=invalid_example
                                        )
                                    else:
                                        response = None
                                elif category == "large_nested_structures":
                                    # Use a more moderate size to avoid memory issues
                                    test_url = f"{target_url}{endpoint}?item_count=1000&nesting_level=3"
                                    request_details = {
                                        "url": test_url,
                                        "method": "POST",
                                        "params": {"item_count": 1000, "nesting_level": 3}
                                    }
                                    response = await client.post(test_url)
                                elif category == "special_characters":
                                    # Get sample payload
                                    examples_url = f"{target_url}/special-characters/examples"
                                    examples_response = await client.get(examples_url)
                                    if examples_response.status_code == 200:
                                        examples = examples_response.json()
                                        rtl_example = examples.get("rtl_example", {})
                                        test_url = f"{target_url}{endpoint}"
                                        request_details = {
                                            "url": test_url,
                                            "method": "POST",
                                            "body": rtl_example
                                        }
                                        response = await client.post(
                                            test_url,
                                            json=rtl_example
                                        )
                                    else:
                                        response = None
                                elif category == "custom":
                                    # Create custom format payload
                                    custom_payload = {
                                        "name": "test_custom_format",
                                        "data": "key1=value1\nkey2=value2\ninvalid line",
                                        "format": "custom"
                                    }
                                    test_url = f"{target_url}{endpoint}"
                                    request_details = {
                                        "url": test_url,
                                        "method": "POST",
                                        "body": custom_payload
                                    }
                                    response = await client.post(
                                        test_url,
                                        json=custom_payload
                                    )
                                else:
                                    # Unsupported category
                                    response = None

                                # Process response
                                if response and response.status_code:
                                    test_result["status_code"] = response.status_code

                                    # Add request details
                                    test_result["details"]["request"] = request_details

                                    # Try to parse response
                                    try:
                                        response_data = response.json()
                                        test_result["details"]["response"] = response_data

                                        # Only save detailed test information to log files if debug is enabled
                                        debug_enabled = vmnf_handler.get('debug', False)
                                        if debug_enabled:
                                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                            test_log_file = f"test_details_{timestamp}.log"
                                            with open(test_log_file, 'w') as f:
                                                json.dump({
                                                    "test_name": test_result.get("name", "Unknown Test"),
                                                    "test_type": test_result.get("test_type", "serialization"),
                                                    "category": test_result.get("category", "unknown"),
                                                    "request": test_result["details"].get("request", {}),
                                                    "response": response_data,
                                                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                }, f, indent=2)

                                            # Print information about the test log file
                                            print(f" → Test details saved to: {test_log_file}")

                                        # Check for error indicators in the response
                                        error_keywords = ["error", "exception", "failed", "invalid"]
                                        found_error = False

                                        for key in error_keywords:
                                            if isinstance(response_data, dict) and key in response_data:
                                                found_error = True
                                                break

                                        if found_error:
                                            test_result["actual_result"] = "VULNERABILITY_FOUND"
                                            test_result["pass"] = False

                                            # Store vulnerability details for interactive payload generation
                                            test_result["vulnerability_details"] = {
                                                "type": "error_based",
                                                "category": category,
                                                "payload": request_details.get("body", {}),
                                                "response": response_data
                                            }

                                            # Check if custom payload generation is requested
                                            set_custom_payload = vmnf_handler.get('set_custom_payload', False)
                                            if set_custom_payload:
                                                # Save detailed test information to log file
                                                log_file = "lasttest.log"
                                                try:
                                                    with open(log_file, 'w') as f:
                                                        json.dump({
                                                            "test": test_result,
                                                            "vulnerability_details": test_result["vulnerability_details"],
                                                            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                        }, f, indent=2)
                                                except Exception as log_error:
                                                    print(f"Error saving test details: {str(log_error)}")

                                                # Launch the interactive payload builder
                                                print(f"\n → Vulnerability found! Launching interactive payload builder...")

                                                try:
                                                    # Use our helper function to launch interactive builder
                                                    launch_interactive_builder_helper(test_result, vmnf_handler)

                                                    # Add test to results and return early to stop testing
                                                    all_test_results[model_name] = {
                                                        "model_name": model_name,
                                                        "fields": {
                                                            "serialization_tests": tests_for_model + [test_result]
                                                        }
                                                    }
                                                    return all_test_results
                                                except Exception as e:
                                                    print(f"\n → Error launching interactive payload builder: {str(e)}")
                                        elif response.status_code >= 400:
                                            test_result["actual_result"] = "ERROR_RESPONSE"
                                            test_result["pass"] = False
                                        else:
                                            # Check for specific category indicators
                                            if category == "circular_references" and "circular" in str(response_data):
                                                test_result["actual_result"] = "VULNERABILITY_FOUND"
                                                test_result["pass"] = False

                                                # Store vulnerability details for interactive payload generation
                                                test_result["vulnerability_details"] = {
                                                    "type": "circular_reference_vulnerability",
                                                    "category": category,
                                                    "payload": request_details.get("body", {}),
                                                    "response": response_data
                                                }

                                                # Check if custom payload generation is requested
                                                set_custom_payload = vmnf_handler.get('set_custom_payload', False)
                                                if set_custom_payload:
                                                    # Save detailed test information to log file
                                                    with open("lasttest.log", 'w') as f:
                                                        json.dump({
                                                            "test": test_result,
                                                            "vulnerability_details": test_result["vulnerability_details"],
                                                            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                        }, f, indent=2)

                                                    # Launch the interactive payload builder
                                                    print(f"\n → Vulnerability found! Launching interactive payload builder...")

                                                    try:
                                                        # Use our helper function to launch interactive builder
                                                        launch_interactive_builder_helper(test_result, vmnf_handler)

                                                        # Add test to results and return early to stop testing
                                                        all_test_results[schema_name] = {
                                                            "model_name": schema_name,
                                                            "fields": {
                                                                "serialization_tests": tests_for_model + [test_result]
                                                            }
                                                        }
                                                        return all_test_results
                                                    except Exception as e:
                                                        print(f"\n → Error launching interactive payload builder: {str(e)}")
                                            elif category == "depth_testing" and response_data.get("depth", 0) > 50:
                                                test_result["actual_result"] = "VULNERABILITY_FOUND"
                                                test_result["pass"] = False

                                                # Store vulnerability details for interactive payload generation
                                                test_result["vulnerability_details"] = {
                                                    "type": "depth_limit_vulnerability",
                                                    "category": category,
                                                    "payload": request_details.get("body", {}),
                                                    "response": response_data
                                                }

                                                # Check if custom payload generation is requested
                                                set_custom_payload = vmnf_handler.get('set_custom_payload', False)
                                                if set_custom_payload:
                                                    # Save detailed test information to log file
                                                    with open("lasttest.log", 'w') as f:
                                                        json.dump({
                                                            "test": test_result,
                                                            "vulnerability_details": test_result["vulnerability_details"],
                                                            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                        }, f, indent=2)

                                                    # Launch the interactive payload builder
                                                    print(f"\n → Vulnerability found! Launching interactive payload builder...")

                                                    try:
                                                        # Use our helper function to launch interactive builder
                                                        launch_interactive_builder_helper(test_result, vmnf_handler)

                                                        # Add test to results and return early to stop testing
                                                        all_test_results[schema_name] = {
                                                            "model_name": schema_name,
                                                            "fields": {
                                                                "serialization_tests": tests_for_model + [test_result]
                                                            }
                                                        }
                                                        return all_test_results
                                                    except Exception as e:
                                                        print(f"\n → Error launching interactive payload builder: {str(e)}")
                                            elif category == "binary_data" and response_data.get("data_type") == "pickle":
                                                test_result["actual_result"] = "VULNERABILITY_FOUND"
                                                test_result["pass"] = False

                                                # Store vulnerability details for interactive payload generation
                                                test_result["vulnerability_details"] = {
                                                    "type": "pickle_deserialization",
                                                    "category": category,
                                                    "payload": request_details.get("body", {}),
                                                    "response": response_data
                                                }

                                                # Check if custom payload generation is requested
                                                set_custom_payload = vmnf_handler.get('set_custom_payload', False)
                                                if set_custom_payload:
                                                    # Save detailed test information to log file
                                                    with open("lasttest.log", 'w') as f:
                                                        json.dump({
                                                            "test": test_result,
                                                            "vulnerability_details": test_result["vulnerability_details"],
                                                            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                        }, f, indent=2)

                                                    # Launch the interactive payload builder
                                                    print(f"\n → Vulnerability found! Launching interactive payload builder...")

                                                    try:
                                                        # Use our helper function to launch interactive builder
                                                        launch_interactive_builder_helper(test_result, vmnf_handler)

                                                        # Add test to results and return early to stop testing
                                                        all_test_results[schema_name] = {
                                                            "model_name": schema_name,
                                                            "fields": {
                                                                "serialization_tests": tests_for_model + [test_result]
                                                            }
                                                        }
                                                        return all_test_results
                                                    except Exception as e:
                                                        print(f"\n → Error launching interactive payload builder: {str(e)}")
                                            else:
                                                test_result["actual_result"] = "SAFE_HANDLING"
                                    except Exception as e:
                                        test_result["actual_result"] = f"RESPONSE_PARSE_ERROR: {str(e)}"
                                        test_result["pass"] = False
                                else:
                                    test_result["actual_result"] = "NO_RESPONSE"
                            except Exception as e:
                                test_result["actual_result"] = f"TEST_ERROR: {str(e)}"
                                test_result["status_code"] = None
                                test_result["pass"] = False
                    else:
                        # If not a serialization test API, mark as informational
                        test_result["actual_result"] = "NOT_TESTED"
                        test_result["description"] = f"Target doesn't appear to be a serialization test API. Tests for {category} not performed."

                    # Add this test to the list
                    tests_for_model.append(test_result)

                # Always display tests as we go for this model - it's a core feature
                try:
                    # Force verbose display for tests
                    display.display_tests_for_model(schema_name, tests_for_model)
                except Exception as e:
                    logger.error(f"Error displaying test results for {schema_name}: {str(e)}")
                    print(f" → Error displaying test results: {str(e)}")

                # Add model to results
                all_test_results[schema_name] = {
                    "model_name": schema_name,
                    "fields": {
                        "serialization_tests": tests_for_model
                    }
                }

        return all_test_results

    # Run the tests
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(perform_serialization_tests(target_url))

    if verbose:
        print(f" → Completed {len(results)} schema tests for serialization vulnerabilities")

    logger.info("Completed serialization tests")
    return results

# Display class for serialization tests
class SerializationTestDisplay:
    """
    Handles the interactive display of serialization test results.
    """
    def __init__(self, colors_disabled=False):
        self.colors_disabled = colors_disabled
        self.test_counter = 0
        self.current_model = None
        self.current_category = None
        self.custom_file_headers_shown = set()  # Track which custom file headers have been shown

    def show_serialization_test(self, model_name, test_result):
        """
        Display a serialization test with its results
        """
        category = test_result.get('category', 'unknown')
        name = test_result.get('name', f'serialization_{category}')
        status_code = test_result.get('status_code')
        actual_result = test_result.get('actual_result', 'UNKNOWN')
        expected_result = test_result.get('expected_result', 'UNKNOWN')
        passed = test_result.get('pass', True)
        description = test_result.get('description', '')
        details = test_result.get('details', {})
        source_file = test_result.get('source_file', '')

        # Show model header when it changes
        if self.current_model != model_name:
            self.current_model = model_name
            if self.test_counter > 0:
                print()
            print(colored(f" Testing Model: {model_name}", 'cyan', attrs=['bold']))
            print("═" * 100)
            # Reset category
            self.current_category = None

        # Show category header when it changes
        if self.current_category != category:
            self.current_category = category

            # Reset custom file headers when category changes
            self.custom_file_headers_shown = set()

            # Show special header for custom tests
            if category.lower() == 'custom':
                print(colored(f"\n CUSTOM SERIALIZATION TESTS", 'yellow', attrs=['bold']))
                print(colored(f" Category: Custom tests are highly customizable test vectors", 'cyan'))
            else:
                print(colored(f"\n Category: {category.upper().replace('_', ' ')}", 'cyan'))

            print("─" * 100)

        # For custom tests from files, show file-specific headers
        if category.lower() == 'custom' and source_file and source_file not in self.custom_file_headers_shown:
            self.custom_file_headers_shown.add(source_file)
            print(colored(f"\n ┌── Custom Tests from: {source_file}", 'yellow', attrs=['bold']))
            print(colored(f" │", 'yellow'))

        self.test_counter += 1

        # Test case header - enhanced for better visibility
        test_prefix = " │ " if category.lower() == 'custom' and source_file else ""

        test_label = f"{test_prefix}Test Case #{self.test_counter}: {name}"
        if not passed:
            test_label = f"{test_label} [VULNERABILITY DETECTED]"

        print(colored(f"\n{test_label}", 'green' if passed else 'red', attrs=['bold' if not passed else None]))

        # Show more detailed description for custom tests
        if category.lower() == 'custom':
            indent = " │ " if source_file else "  "
            print(colored(f"{indent}Test Description:", 'yellow', attrs=['bold']))
            print(f"{indent}{description}")
            print(f"{indent}Expected Result: {colored(expected_result, 'blue')}")

            # Show source file if it exists and we're not already showing file headers
            if source_file and len(self.custom_file_headers_shown) > 1:  # More than one file
                print(f"{indent}Source: {colored(source_file, 'green')}")
        else:
            print(colored(f"  {description}", 'white'))

        # Request details if available
        if details.get('request'):
            print(colored("\nRequest Details:", 'blue'))
            req_data = details['request']
            if isinstance(req_data, dict):
                # Format as JSON
                req_json = json.dumps(req_data, indent=2)
                for line in req_json.splitlines():
                    print(f"  {line}")
            else:
                print(f"  {req_data}")

        # Response details if available
        if details.get('response'):
            print(colored("\nResponse:", 'blue'))
            resp_data = details['response']

            # Show status code if available
            if status_code:
                status_color = 'green' if status_code < 400 else 'red'
                print(f"  Status: {colored(status_code, status_color)}")

            # Format response body
            if isinstance(resp_data, dict):
                # Check size to avoid memory issues
                resp_str = str(resp_data)
                if len(resp_str) > 2000:
                    # Truncate very large responses
                    print(f"  Response too large to display ({len(resp_str)} chars). Showing summary:")
                    summary = {k: v if not isinstance(v, (dict, list)) or k == 'message' or k == 'error'
                              else f"[{type(v).__name__} with {len(v)} items]"
                              for k, v in resp_data.items()}
                    resp_json = json.dumps(summary, indent=2)
                    for line in resp_json.splitlines():
                        print(f"  {line}")
                else:
                    # Show full response for reasonable sizes
                    resp_json = json.dumps(resp_data, indent=2)
                    for line in resp_json.splitlines():
                        print(f"  {line}")
            else:
                # Truncate large string responses
                resp_str = str(resp_data)
                if len(resp_str) > 1000:
                    print(f"  {resp_str[:1000]}... [truncated, {len(resp_str)} chars total]")
                else:
                    print(f"  {resp_data}")

        # Show test result
        result_color = 'green' if passed else 'red'
        result_symbol = '✓' if passed else '✗'

        print("\nTest Result:")
        print(f"  Status: {colored(result_symbol, result_color)} {colored(actual_result, result_color)}")
        print(f"  Expected: {expected_result}")

        # Add separator between tests
        print("\n" + "─" * 100)

    def display_tests_for_model(self, model_name, tests):
        """Display all tests for a specific model"""
        if not tests:
            print(colored(f"\n No test results available for model: {model_name}", 'yellow'))
            print(colored(" This could be because:", 'yellow'))
            print(" - The API endpoint returned no results")
            print(" - The test category doesn't apply to this model")
            print(" - There was an error during test execution")
            print(" - The target service is unavailable")
            print("\nPlease check your API connection and test configuration.")
            return

        # Show tests
        for test in tests:
            self.show_serialization_test(model_name, test)

# Integration with PydanticTester in pydantic_engine.py
def integrate_serialization_tests(test_runner, model_name, schema_def):
    """
    Helper function to integrate serialization tests into the existing PydanticTester.

    Args:
        test_runner: The PydanticTestRunner instance
        model_name: Name of the model to test
        schema_def: Schema definition for the model

    Returns:
        Serialization test results for the model
    """
    # This is a placeholder for integration code
    # In a real implementation, this would create appropriate model classes
    # and run the serialization tests on them

    # For now, we're just returning a placeholder
    return {
        "name": "serialization_integration",
        "test_type": "serialization",
        "description": "Integration point for serialization tests",
        "expected_result": "INTEGRATED",
        "actual_result": "SUCCESS",
        "pass": True
    }