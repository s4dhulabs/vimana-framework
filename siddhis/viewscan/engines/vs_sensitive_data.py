import os
import sys
import ast
import json
import inspect
from time import sleep
from neotermcolor import cprint,colored as cl
from ..tools.vs_tools import (
        docme,
        is_POST_request, 
        check_match, 
        KeywordVisitor, 
        extract_post_params,
        inspect_decorator
)


class vs_sensitive_data:
    def __init__(self, **options:dict) -> None:
        self.options = options
        self.object = options.get("obj_name")
        self.issues = []
        self.decorators = self.options['dec_args']
        self.node_tracker = []
        self.dec_inspector = inspect_decorator()
        self.__load_settings__()

    def __load_settings__(self):
        file_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        with open(file_path, 'r') as f:
            settings = json.load(f)
            for key, value in settings.items():
                setattr(self, key, value)
        
    def __show_code__(self, source_code:list=False):
        if not source_code:
            source_code = self.options.get('hl_code')

        print()
        print()
        for line in source_code:
            print(line, end='')
        print()

    def sensitive_information_filtering(self, node:ast.AST=False, finished:bool=True):
        '''
        The function doesn't prevent the values of sensitive variables from being leaked.

        Django offers a set of function decorators to help you
        control which information should be filtered out of error
        reports in a production environment (that is, where DEBUG is
        set to False): sensitive_variables() and
        sensitive_post_parameters().

        * sensitive_variables

        If a function (either a view or any regular callback) in
        your code uses local variables susceptible to contain
        sensitive information, you may prevent the values of those
        variables from being included in error reports using the
        sensitive_variables decorator.
        
        To systematically hide all local variables of a function
        from error logs, do not provide any argument to the
        sensitive_variables decorator: sensitive_variables()
       
        * sensitive_post_parameters

        If one of your views receives an HttpRequest object with
        POST parameters susceptible to contain sensitive
        information, you may prevent the values of those parameters
        from being included in the error reports using the
        sensitive_post_parameters decorator.

        https://docs.djangoproject.com/en/4.1/howto/error-reporting/#filtering-sensitive-information
        '''
        
        if not node:
            node = self.options.get('node')

        self.decorator_type = 'sensitive_variables'
        self.variables = []

        def run_inspector():
            return(
                self.dec_inspector.run(
                    self.object, 
                    self.decorator_type, 
                    self.decorators, 
                    self.variables
                )
            )
        
        if isinstance(node, (ast.Call,)):
            if isinstance(node.func, ast.Attribute):
                for keyword in node.keywords:
                    if keyword.arg in self.sensitive_params:
                        self.variables.append(keyword.arg)
                        if is_POST_request(keyword):
                            self.decorator_type = 'sensitive_post_parameters'
                        else:
                            self.decorator_type = 'sensitive_variables'
                            self.issues.append(keyword.arg)

        elif isinstance(node, ast.Name) and node.id in self.sensitive_params:
            self.decorator_type = 'sensitive_variables'
            self.variables.append(node.id)

        elif isinstance(node, ast.FunctionDef):
            post_params = extract_post_params(node)
            if post_params:
                self.decorator_type = 'sensitive_post_parameters'
                self.variables.extend(
                        [p for p in post_params if p in self.sensitive_params]
                    )
            else:
                self.decorator_type = 'sensitive_variables'
                visitor = KeywordVisitor(self.sensitive_params)
                visitor.visit(node)
                keywords = visitor.keywords
                self.variables.extend(
                        [k for k in keywords if k in self.sensitive_params]
                    )

        if self.variables:
            self.issues.extend(run_inspector())
        
        for child in ast.iter_child_nodes(node):
            self.node_tracker.append(child)
            self.sensitive_information_filtering(child,False)
        
        if finished and self.issues:
            self.__show_code__()
            docme(self.issues)
        
    def __status__(self, test_type):
        status_msg = (f"    → Running {cl(test_type, 'red')} tests against {self.object}...")
        print(status_msg.ljust(os.get_terminal_size().columns - 1), end="\r")
        sleep(0.04)

    def __start_scan__(self):
        [self.__status__(vst) or getattr(self,vst)() \
            for vst in dir(self) if callable(getattr(self, vst)) \
                and not vst.startswith("__")]

