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

from pygments import formatters, highlight, lexers
from neotermcolor import cprint, colored
from simple_term_menu import TerminalMenu
from typing import Dict, List, Any, Optional
from core.vmnf_navicontrols import build_options, normalize
import shutil
import json
import sys
import os
import re

class PydanticNaviHandler:
    """
    Navigation handler for Pydantic test results.
    """
    
    def __init__(self, vmnf_handler: Dict[str, Any], test_results: Dict[str, Any]) -> None:
        """
        Initialize the navigation handler.
        
        Args:
            vmnf_handler: Vimana framework handler
            test_results: Pydantic test results
        """
        self.vmnf_handler = vmnf_handler
        self.test_results = test_results
        self.prompt = '➤ '
        self.accepted_keys = (
            "enter", "o", "f", "t", "r", "s", "d", "b", "u", 'y', 'p', 'ctrl-y', 'i', 'e', 'q'
        )
        self.detailed_enabled = False
        self.current_model = None
        self.current_field = None
        self.current_view = 'models'  # 'models', 'fields', 'tests'
        self.lexer_style = 'Python3'
        
    def get_terminal_height(self) -> int:
        """Get terminal height."""
        return shutil.get_terminal_size().lines
        
    def get_terminal_width(self) -> int:
        """Get terminal width."""
        return shutil.get_terminal_size().columns
        
    def build_model_items(self) -> List[Dict[str, Any]]:
        """
        Build items for model list view.
        
        Returns:
            List of model items
        """
        items = []
        
        for model_name, model_data in self.test_results.items():
            total_tests = 0
            passed_tests = 0
            
            for field_name, field_tests in model_data.get('fields', {}).items():
                for test in field_tests:
                    total_tests += 1
                    if test.get('pass', False):
                        passed_tests += 1
            
            path = model_data.get('path', '')
            method = model_data.get('method', '').upper()
            operation_id = model_data.get('operation_id', '')
            
            items.append({
                'Model': model_name,
                'Path': path,
                'Method': method,
                'OperationId': operation_id,
                'Tests': total_tests,
                'Passed': passed_tests,
                'Failed': total_tests - passed_tests,
                'PassRate': f"{(passed_tests / total_tests * 100) if total_tests else 0:.1f}%"
            })
            
        return items
        
    def build_field_items(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Build items for field list view.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of field items
        """
        items = []
        model_data = self.test_results.get(model_name, {})
        
        for field_name, field_tests in model_data.get('fields', {}).items():
            total_tests = len(field_tests)
            passed_tests = sum(1 for test in field_tests if test.get('pass', False))
            
            # Get field type from first test
            field_type = "unknown"
            if field_tests:
                field_type = field_tests[0].get('field_type', "unknown")
            
            items.append({
                'Field': field_name,
                'Type': field_type,
                'Tests': total_tests,
                'Passed': passed_tests,
                'Failed': total_tests - passed_tests,
                'PassRate': f"{(passed_tests / total_tests * 100) if total_tests else 0:.1f}%"
            })
            
        return items
        
    def build_test_items(self, model_name: str, field_name: str) -> List[Dict[str, Any]]:
        """
        Build items for test list view.
        
        Args:
            model_name: Name of the model
            field_name: Name of the field
            
        Returns:
            List of test items
        """
        items = []
        model_data = self.test_results.get(model_name, {})
        field_tests = model_data.get('fields', {}).get(field_name, [])
        
        for i, test in enumerate(field_tests):
            result = "✓" if test.get('pass', False) else "✗"
            expected = test.get('expected_result', '')
            actual = test.get('actual_result', '')
            status_code = test.get('status_code', '')
            
            items.append({
                'ID': i + 1,
                'Test': test.get('name', ''),
                'Type': test.get('test_type', ''),
                'Result': result,
                'Expected': expected,
                'Actual': actual,
                'StatusCode': status_code
            })
            
        return items
    
    def test_preview(self, option_index: str) -> str:
        """
        Generate preview for a test.
        
        Args:
            option_index: Selected option index
            
        Returns:
            Preview text
        """
        # Extract ID from the option
        match = re.search(r'^\s*(\d+)', option_index)
        if not match:
            return "Invalid selection"
            
        test_id = int(match.group(1)) - 1
        
        # Get test data
        model_data = self.test_results.get(self.current_model, {})
        field_tests = model_data.get('fields', {}).get(self.current_field, [])
        
        if test_id < 0 or test_id >= len(field_tests):
            return "Invalid test ID"
            
        test = field_tests[test_id]
        
        # Format preview
        preview = []
        preview.append(f"Test: {test.get('name', '')}")
        preview.append(f"Type: {test.get('test_type', '')}")
        preview.append(f"Description: {test.get('description', '')}")
        preview.append("")
        preview.append(f"Value: {json.dumps(test.get('value', ''), indent=2)}")
        preview.append("")
        preview.append(f"Expected Result: {test.get('expected_result', '')}")
        preview.append(f"Actual Result: {test.get('actual_result', '')}")
        preview.append(f"Status Code: {test.get('status_code', '')}")
        preview.append(f"Passed: {test.get('pass', False)}")
        preview.append("")
        
        # Add response body if available
        response_body = test.get('response_body')
        if response_body:
            preview.append("Response Body:")
            try:
                if isinstance(response_body, str):
                    preview.append(response_body)
                else:
                    preview.append(json.dumps(response_body, indent=2))
            except:
                preview.append(str(response_body))
        
        # Format and highlight
        preview_text = "\n".join(preview)
        lexer = lexers.get_lexer_by_name(self.lexer_style, stripnl=False, stripall=False)
        formatter = formatters.TerminalFormatter(bg="dark")
        return highlight(preview_text, lexer, formatter)
        
    def field_preview(self, option_index: str) -> str:
        """
        Generate preview for a field.
        
        Args:
            option_index: Selected option index
            
        Returns:
            Preview text
        """
        # Extract field name from the option
        match = re.search(r'^\s*\S+\s+(\S+)', option_index)
        if not match:
            return "Invalid selection"
            
        field_name = match.group(1)
        
        # Get field data
        model_data = self.test_results.get(self.current_model, {})
        field_tests = model_data.get('fields', {}).get(field_name, [])
        
        if not field_tests:
            return "No tests found for this field"
            
        # Format preview
        preview = []
        preview.append(f"Field: {field_name}")
        
        # Get field type from first test
        field_type = "unknown"
        if field_tests:
            field_type = field_tests[0].get('field_type', "unknown")
        
        preview.append(f"Type: {field_type}")
        preview.append("")
        
        # Add test summary
        total_tests = len(field_tests)
        passed_tests = sum(1 for test in field_tests if test.get('pass', False))
        failed_tests = total_tests - passed_tests
        pass_rate = f"{(passed_tests / total_tests * 100) if total_tests else 0:.1f}%"
        
        preview.append(f"Total Tests: {total_tests}")
        preview.append(f"Passed: {passed_tests}")
        preview.append(f"Failed: {failed_tests}")
        preview.append(f"Pass Rate: {pass_rate}")
        preview.append("")
        
        # Add brief summary of each test
        preview.append("Tests:")
        for i, test in enumerate(field_tests):
            result = "✓" if test.get('pass', False) else "✗"
            preview.append(f"  {i+1}. {result} {test.get('name', '')}")
        
        # Format and highlight
        preview_text = "\n".join(preview)
        lexer = lexers.get_lexer_by_name(self.lexer_style, stripnl=False, stripall=False)
        formatter = formatters.TerminalFormatter(bg="dark")
        return highlight(preview_text, lexer, formatter)
        
    def model_preview(self, option_index: str) -> str:
        """
        Generate preview for a model.
        
        Args:
            option_index: Selected option index
            
        Returns:
            Preview text
        """
        # Extract model name from the option
        match = re.search(r'^\s*\S+\s+(\S+)', option_index)
        if not match:
            return "Invalid selection"
            
        model_name = match.group(1)
        
        # Get model data
        model_data = self.test_results.get(model_name, {})
        
        if not model_data:
            return "Model not found"
            
        # Format preview
        preview = []
        preview.append(f"Model: {model_name}")
        preview.append(f"Path: {model_data.get('path', '')}")
        preview.append(f"Method: {model_data.get('method', '').upper()}")
        preview.append(f"Operation ID: {model_data.get('operation_id', '')}")
        preview.append("")
        
        # Add field summary
        fields = model_data.get('fields', {})
        preview.append(f"Fields: {len(fields)}")
        
        for field_name, field_tests in fields.items():
            total_tests = len(field_tests)
            passed_tests = sum(1 for test in field_tests if test.get('pass', False))
            preview.append(f"  - {field_name}: {passed_tests}/{total_tests} tests passed")
            
        # Format and highlight
        preview_text = "\n".join(preview)
        lexer = lexers.get_lexer_by_name(self.lexer_style, stripnl=False, stripall=False)
        formatter = formatters.TerminalFormatter(bg="dark")
        return highlight(preview_text, lexer, formatter)
        
    def export_results(self, format: str = 'json') -> None:
        """
        Export test results.
        
        Args:
            format: Export format (json, html, pdf)
        """
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            filename = f"jcolt_pydantic_tests_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2)
                
            print(f"\nResults exported to {filename}")
            
        elif format == 'html':
            # Simple HTML export
            filename = f"jcolt_pydantic_tests_{timestamp}.html"
            
            with open(filename, 'w') as f:
                # Write HTML header
                f.write("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>JColt Pydantic Test Results</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1, h2, h3 { color: #333; }
                        .model { margin-bottom: 30px; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
                        .field { margin-bottom: 20px; }
                        .test { margin-bottom: 10px; padding: 10px; border-radius: 3px; }
                        .pass { background-color: #e6ffe6; }
                        .fail { background-color: #ffe6e6; }
                        .details { font-family: monospace; white-space: pre-wrap; background-color: #f5f5f5; padding: 10px; border-radius: 3px; }
                    </style>
                </head>
                <body>
                    <h1>JColt Pydantic Test Results</h1>
                """)
                
                # Write models
                for model_name, model_data in self.test_results.items():
                    f.write(f'<div class="model">')
                    f.write(f'<h2>Model: {model_name}</h2>')
                    f.write(f'<p>Path: {model_data.get("path", "")}</p>')
                    f.write(f'<p>Method: {model_data.get("method", "").upper()}</p>')
                    
                    # Write fields
                    for field_name, field_tests in model_data.get('fields', {}).items():
                        f.write(f'<div class="field">')
                        f.write(f'<h3>Field: {field_name}</h3>')
                        
                        # Write tests
                        for test in field_tests:
                            result_class = "pass" if test.get('pass', False) else "fail"
                            f.write(f'<div class="test {result_class}">')
                            f.write(f'<p><strong>Test:</strong> {test.get("name", "")}</p>')
                            f.write(f'<p><strong>Type:</strong> {test.get("test_type", "")}</p>')
                            f.write(f'<p><strong>Description:</strong> {test.get("description", "")}</p>')
                            f.write(f'<p><strong>Expected:</strong> {test.get("expected_result", "")}</p>')
                            f.write(f'<p><strong>Actual:</strong> {test.get("actual_result", "")}</p>')
                            f.write(f'<p><strong>Status:</strong> {test.get("status_code", "")}</p>')
                            
                            # Add test value
                            value = test.get('value', '')
                            if value:
                                try:
                                    if isinstance(value, str):
                                        f.write(f'<p><strong>Value:</strong> "{field_name}"</p>')
                                    else:
                                        f.write(f'<p><strong>Value:</strong></p>')
                                        f.write(f'<div class="details">{json.dumps(field_name, indent=2)}</div>')
                                except:
                                    f.write(f'<p><strong>Value:</strong> {str(field_name)}</p>')
                            
                            # Add response body
                            response_body = test.get('response_body')
                            if response_body:
                                f.write(f'<p><strong>Response:</strong></p>')
                                try:
                                    if isinstance(response_body, str):
                                        f.write(f'<div class="details">{response_body}</div>')
                                    else:
                                        f.write(f'<div class="details">{json.dumps(response_body, indent=2)}</div>')
                                except:
                                    f.write(f'<div class="details">{str(response_body)}</div>')
                            
                            f.write('</div>')
                        
                        f.write('</div>')
                    
                    f.write('</div>')
                
                # Write HTML footer
                f.write("""
                </body>
                </html>
                """)
                
            print(f"\nResults exported to {filename}")
            
        else:
            print(f"\nUnsupported export format: {format}")
        
    def manage(self) -> None:
        """
        Manage the navigation interface.
        """
        hcolor = 'green'
        random_banner = 'default_naviban'
        show_banner = False
        keep_banner = 'default_naviban'
        preview_command = None
        self.preview_title = " ~ Pydantic Test Details ~"
        
        # Start with model view
        self.current_view = 'models'
        
        while True:
            # Build items based on current view
            if self.current_view == 'models':
                items = self.build_model_items()
                headers = ['Model', 'Path', 'Method', 'Tests', 'Passed', 'Failed', 'PassRate']
                preview_command = self.model_preview
                
            elif self.current_view == 'fields':
                if not self.current_model:
                    self.current_view = 'models'
                    continue
                    
                items = self.build_field_items(self.current_model)
                headers = ['Field', 'Type', 'Tests', 'Passed', 'Failed', 'PassRate']
                preview_command = self.field_preview
                
            elif self.current_view == 'tests':
                if not self.current_model or not self.current_field:
                    self.current_view = 'fields'
                    continue
                    
                items = self.build_test_items(self.current_model, self.current_field)
                headers = ['ID', 'Test', 'Type', 'Result', 'Expected', 'Actual', 'StatusCode']
                preview_command = self.test_preview
                
            else:
                # Invalid view, go back to models
                self.current_view = 'models'
                continue
            
            # Build menu options
            _options_, header = build_options(items, headers, False)
            header_size = len(header)
            
            print('\033[2J\033[1;1H')  # Clear screen
            
            # Add navigation information
            navigation_header = f" JColt Pydantic Testing Results"
            if self.current_view == 'fields':
                navigation_header += f" > {self.current_model}"
            elif self.current_view == 'tests':
                navigation_header += f" > {self.current_model} > {self.current_field}"
                
            navigation_header += " | [Enter] Drill Down | [b] Back | [e] Export | [q] Quit"
            
            fuzzmenu = TerminalMenu(
                menu_entries=_options_,
                preview_command=preview_command,
                menu_cursor=self.prompt,
                show_search_hint=True,
                show_search_hint_text=" ",
                accept_keys=self.accepted_keys,
                preview_title=self.preview_title,
                preview_size=self.get_terminal_height() - 1,
                title=navigation_header
            )
            
            kbann = normalize(
                header, hcolor, 'msg', show_banner, 
                random_banner, keep_banner, header_size, False
            )
            keep_banner = kbann
            
            fuzz_index = fuzzmenu.show()
            
            if fuzz_index is None:
                print('\033[2J\033[1;1H')
                break
                
            chosen_key = fuzzmenu._chosen_accept_key
            
            if chosen_key == 'q':
                print('\033[2J\033[1;1H')
                break
                
            elif chosen_key == 'b':
                # Go back one level
                if self.current_view == 'tests':
                    self.current_view = 'fields'
                    self.current_field = None
                elif self.current_view == 'fields':
                    self.current_view = 'models'
                    self.current_model = None
                elif self.current_view == 'models':
                    print('\033[2J\033[1;1H')
                    break
                    
            elif chosen_key == 'e':
                # Export results
                format_menu = TerminalMenu(
                    ["JSON", "HTML", "Cancel"],
                    title="Select export format:"
                )
                format_index = format_menu.show()
                
                if format_index == 0:
                    self.export_results('json')
                elif format_index == 1:
                    self.export_results('html')
                
                # Pause to show message
                input("\nPress Enter to continue...")
                
            elif chosen_key == 'p':
                if preview_command is None:
                    if self.current_view == 'models':
                        preview_command = self.model_preview
                    elif self.current_view == 'fields':
                        preview_command = self.field_preview
                    elif self.current_view == 'tests':
                        preview_command = self.test_preview
                else:
                    preview_command = None
                    
            elif chosen_key == 'ctrl-y':
                import random
                from core.vmnf_navicontrols import srandlexers
                self.lexer_style = random.choice(srandlexers)
                
            elif chosen_key == "enter":
                if fuzz_index < 0 or fuzz_index >= len(_options_):
                    continue
                    
                selected_option = _options_[fuzz_index]
                
                if self.current_view == 'models':
                    # Extract model name
                    match = re.search(r'^\s*\S+\s+(\S+)', selected_option)
                    if match:
                        self.current_model = match.group(1)
                        self.current_view = 'fields'
                        
                elif self.current_view == 'fields':
                    # Extract field name
                    match = re.search(r'^\s*\S+\s+(\S+)', selected_option)
                    if match:
                        self.current_field = match.group(1)
                        self.current_view = 'tests'