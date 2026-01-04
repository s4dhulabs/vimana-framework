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
from colorama import Fore, Style, init
from fastapi.testclient import TestClient
from jsonschema import validate, ValidationError, RefResolver
import requests
import json
from pygments import highlight, lexers, formatters

# Inicializa a colorama
init(autoreset=True)

class ValidateSchema:
    def __init__(self, openapi_schema, spec_id, vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.verbose = vmnf_handler.get('verbose')
        self.show_response = vmnf_handler.get('show_response')
        self.pretty_output = vmnf_handler.get('pretty_output', False)
        self.openapi_schema = openapi_schema
        spec_info = VFDBOps().get_by_id('_SPECS_', 'spec_id', spec_id)
        self.host = spec_info.spec_host
        self.client = TestClient(self.create_app())
        self.timeout = 10  # Timeout padrão de 10 segundos

    def create_app(self):
        from fastapi import FastAPI
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        from urllib.parse import urlparse, urlunparse

        app = FastAPI()

        class HostMiddleware(BaseHTTPMiddleware):
            def __init__(self, app, host):
                super().__init__(app)
                self.host = host

            async def dispatch(self, request: Request, call_next):
                url = urlparse(str(request.url))
                new_url = urlunparse((url.scheme, self.host.replace('http://', '').replace('https://', ''), url.path, url.params, url.query, url.fragment))
                request._url = new_url
                response = await call_next(request)
                return response

        app.add_middleware(HostMiddleware, host=self.host)
        return app

    def get_response_schema(self, endpoint, method):
        try:
            return self.openapi_schema["paths"][endpoint][method]["responses"]["200"]["content"]["application/json"]["schema"]
        except KeyError:
            return None

    def get_request_schema(self, endpoint, method):
        return self.openapi_schema["paths"][endpoint][method].get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})

    def validate_schema(self, endpoint, method):
        response_schema = self.get_response_schema(endpoint, method)
        request_schema = self.get_request_schema(endpoint, method)
        headers = {}
        data = None

        if self.pretty_output:
            icon_failed = "❌"
            icon_passed = "✅"
        else:
            icon_failed = "[FAIL]→"
            icon_passed = "[PASS]→"

        if endpoint == '/docker_logs/{container_id}':
            endpoint = '/docker_logs/feb968a7da0c52c5e283f0032df4190d2148680001fc7972005e45e5a412cd28'

        if endpoint == "/token":
            data = json.dumps({"username": "s4dhu", "password": "secret"})
        elif method == "post":
            data = json.dumps({"key": "value"})
        else:
            headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzNGRodSIsImV4cCI6MTcyNDY3OTQ3M30.u6QSqFaTQCHrXSBspxk_60uzYDbLgNlk3JQYD8TuiBM"}

        url = f"http://{self.host.replace('http://', '').replace('https://', '')}{endpoint}"

        try:
            response = requests.request(method.upper(), url, headers=headers, data=data, timeout=self.timeout)
            if response.status_code == 405:
                self.print_message(f"Method Not Allowed at {url}", "yellow", icon_failed)
                return
            elif response.status_code == 401:
                self.print_message(f"Unauthorized at {url}", "yellow", icon_failed)
                return
            elif response.status_code == 422:
                self.print_message(f"Unprocessable Entity at {url}", "yellow",icon_failed)
                if self.verbose or self.show_response:
                    self.print_response(response)
                return
            elif response.status_code != 200:
                self.print_message(f"Server not reachable at {url}", "red", icon_failed)
                return
        except requests.ConnectionError:
            self.print_message(f"Failed to connect to server at {url}", "red", icon_failed)
            return
        except requests.Timeout:
            self.print_message(f"Request to {url} timed out.", "red", icon_failed)
            return

        resolver = RefResolver(base_uri='', referrer=self.openapi_schema)
        try:
            validate(instance=response.json(), schema=response_schema, resolver=resolver)
            self.print_message(f"Schema validation passed for endpoint {endpoint}", "green", icon_passed)
        except ValidationError as e:
            self.print_message(f"Schema validation failed for endpoint {endpoint}: {e.message}", "red", icon_failed)

        if self.verbose or self.show_response:
            self.print_response(response)

    def print_message(self, message, color, icon):
        if self.pretty_output:
            color_map = {
                "red": Fore.RED,
                "green": Fore.GREEN,
                "yellow": Fore.YELLOW
            }
            print(f"    {icon} {color_map[color]}{message}{Style.RESET_ALL}")
        else:
            print(f"   {icon} {message}")

    def print_response(self, response):
        try:
            response_json = response.json()
            formatted_json = json.dumps(response_json, indent=4, ensure_ascii=False)
            if self.pretty_output:
                splited_response = formatted_json.find("\\n")
                if splited_response != -1:
                    formatted_json = "\n".join([i for i in formatted_json.split("\\n")])
                    highlighted_text = highlight(formatted_json, lexers.PythonTracebackLexer(), formatters.TerminalFormatter())
                    print(highlighted_text)
                else:
                    highlighted_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter())
                    indented_json = "\n".join(["\t" + line for line in highlighted_json.split("\n")])
                    print(indented_json)
            else:   
                print(json.dumps(response_json, indent=4, ensure_ascii=False))
        except json.JSONDecodeError:
            response_text = response.text
            if self.pretty_output:
                indented_text = "\n".join(["\t" + line for line in response_text.split("\n")])
                print(indented_text)
            else:
                print(response_text)

    def run_schema_validation(self):
        for path, methods in self.openapi_schema["paths"].items():

            print(f"⚙️  Validating schema for path {path}: {','.join(methods.keys()).upper()}")

            for method in methods:
                self.validate_schema(path, method)

                if self.verbose or self.show_response:
                    print('-' * 100)

        print()
        
    def run(self):
        self.run_schema_validation()