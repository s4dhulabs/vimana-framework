import asyncio
import aiohttp
from neotermcolor import colored
from ..utils import *
import shutil
import json

class jcShow:
    def __init__(self, l_fuzzscope:int=30, silent_mode:bool=False):
        self.req_controller = 0
        self.len_fuzzscope = l_fuzzscope
        self.silent_mode = silent_mode

    async def get_response_text(self, response):
        try:
            return await response.json()
        except aiohttp.client_exceptions.ContentTypeError:
            return await response.text()

    def show_response_dict(self, data):
        if self.silent_mode:
            result = []
            for k, v in data.items():
                if isinstance(v, list):
                    result.append(f" {k:>15}:")
                    for e in v:
                        if isinstance(e, dict):
                            for x, y in e.items():
                                result.append(f" {x:>20} {y}")
                            result.append("")
                        else:
                            result.append(f"\t+ {e}")
                else:
                    result.append(f" {k:>15}: {v}")
            return "\n".join(result)
        else:
            for k, v in data.items():
                if isinstance(v, list):
                    print(f" {k:>15}:")
                    for e in v:
                        if isinstance(e, dict):
                            for x, y in e.items():
                                print(f" {x:>20} {y}")
                            print()
                        else:
                            print(f"\t+ {e}")
                else:
                    print(f" {k:>15}: {v}")

    def show_request_info(self, method, path, version, headers, body):
        if self.silent_mode:
            request_info = f"{method} {path} HTTP/{version.major}.{version.minor}\n"
            for k, v in headers.items():
                request_info += f"{k}: {v}\n"
            if body:
                request_info += f"{body}\n"
            return request_info
        else:
            m_color = method_colors.get(method.upper(), None)
            dec_method = colored(method, m_color, attrs=['bold'])

            print(f" {dec_method} {colored(path, 242)} HTTP/{version.major}.{version.minor}")
            for k, v in headers.items():
                print(f" {colored(k, 12)}: {colored(v, 29)}")
            print()
            if body:
                print(f" {colored(body, 29)}")
            
    def show_response_info(self, response, response_text):
        if self.silent_mode:
            resp_prot_version = f'HTTP/{response.version.major}.{response.version.minor}'
            status_code = response.status
            status_message = response.reason

            response_info = f"{resp_prot_version} {status_code} {status_message}\n"
            for k, v in response.headers.items():
                response_info += f"{k}: {v}\n"
            
            
            response_info += "\n" + self.show_response_body(response_text)
            return response_info
        else:
            resp_prot_version = f'HTTP/{response.version.major}.{response.version.minor}'
            status_code = response.status
            status_message = response.reason

            print("-" * 70)

            print(f" {resp_prot_version} {status_code} {status_message}")
            for k, v in response.headers.items():
                print(f' {k}: {colored(v, 242)}')
            print()

            self.show_response_body(response_text)
            
            self.req_controller += 1
            if self.req_controller != self.len_fuzzscope:
                print("\u2500" * 104)  
 
    def show_response_body(self, response_text):
        if self.silent_mode:
            if isinstance(response_text, str):
                return ' ' + response_text
            elif isinstance(response_text, list):
                return "\n".join([self.show_response_dict(item) for item in response_text if self.show_response_dict(item) is not None])
            else:
                return self.show_response_dict(response_text)
        else:
            if isinstance(response_text, str):
                print(' ' + response_text)
            elif isinstance(response_text, list):
                for item in response_text:
                    self.show_response_dict(item)
            else:
                self.show_response_dict(response_text)

    def fuzz_test_preview(self, option_index, request_info, response_info):
        terminal_width = shutil.get_terminal_size().columns
        column_width = terminal_width // 2

        request_lines = request_info.split('\n')
        response_lines = response_info.split('\n')

        preview_lines = []
        for req_line, res_line in zip(request_lines, response_lines):
            preview_lines.append(f"{req_line:<{column_width}} | {res_line:<{column_width}}")

        if len(request_lines) > len(response_lines):
            for req_line in request_lines[len(response_lines):]:
                preview_lines.append(f"{req_line:<{column_width}} | {'':<{column_width}}")
        elif len(response_lines) > len(request_lines):
            for res_line in response_lines[len(request_lines):]:
                preview_lines.append(f"{'':<{column_width}} | {res_line:<{column_width}}")

        preview_text = "\n".join(preview_lines)
        return preview_text

class PydanticTestDisplay:
    def __init__(self, colors_disabled=False):
        self.colors_disabled = colors_disabled
        self.test_counter = 0
        self.current_model = None
        
    def extract_test_info(self, summary):
        """Extract model name and test type from summary"""
        if not summary:
            return None, summary
            
        # Remove "Test " prefix if present
        if summary.startswith('Test '):
            summary = summary[5:]
            
        # Split into model and test type if possible
        if ' - ' in summary:
            model_field = summary.split(' - ')[0]
            model_name = model_field.split('.')[0] if '.' in model_field else model_field
            return model_name, summary
        
        return None, summary

    def show_test_request(self, fuzz_obj):
        """Display Pydantic test request with all details"""
        properties = fuzz_obj.get('properties', {})
        summary = properties.get('summary', '')
        model_name, test_summary = self.extract_test_info(summary)
        model_field = test_summary.split(" - ")[0].split(".")[1]

        # Show model header when it changes
        if self.current_model != model_name:
            self.current_model = model_name
            # Only print separator if this isn't our first model
            if self.test_counter > 0:
                print()
            print(colored(f" Testing Model: {model_name} → {model_field}", 'cyan', attrs=['bold']))
            print(f"{'═' * 100}")
        
        self.test_counter += 1
        
        # Test case header with full summary (minus "Test " prefix)
        print(colored(f"\n▶ Test Case #{self.test_counter}: {test_summary}", 'green'))
        print(colored(f"  Operation: {properties.get('operationId', 'Unknown')}", 'green'))
        print()
        
        # Show request details
        print(colored("Request:", 'green'))
        print(f"  Method: {colored(fuzz_obj['method'].upper(), 'blue')}")
        print(f"  Endpoint: {colored(fuzz_obj['path'], 'blue')}")
        
        # Show request body if present
        if fuzz_obj.get('body'):
            print("  Body:")
            body_json = json.dumps(fuzz_obj['body'], indent=4)
            for line in body_json.splitlines():
                print(f"    {colored(line, 'white')}")

    def show_test_response(self, fuzz_obj):
        """Display Pydantic test response with all details"""
        response = fuzz_obj.get('response')
        response_text = fuzz_obj.get('response_text')
        response_audit = fuzz_obj.get('response_status_audit', {})
        
        if not response:
            return
            
        print("\nResponse:")
        print(f"  Status: {colored(response.status, 'blue')}")
        
        # Show response body
        if response_text:
            print("  Body:")
            if isinstance(response_text, dict):
                resp_json = json.dumps(response_text, indent=4)
                for line in resp_json.splitlines():
                    print(f"    {colored(line, 'white')}")
            else:
                print(f"    {colored(response_text, 'white')}")
        
        # Show test result based on status code
        expected_codes = response_audit.get('expected_status_codes', [])
        actual_code = response_audit.get('actual_status_code')
        status_mismatch = response_audit.get('status_mismatch', False)
        
        result_symbol = '✗' if status_mismatch else '✓'
        result_color = 'red' if status_mismatch else 'green'
        
        print("\nTest Result:")
        print(f"  Status: {colored(result_symbol, result_color)}")
        print(f"  Expected Status Codes: {expected_codes}")
        print(f"  Actual Status Code: {actual_code}")
        
        # Add a simple line separator between tests
        print("\n" + "─" * 100)


