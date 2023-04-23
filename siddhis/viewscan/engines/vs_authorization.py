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
import sys

sys.path.append('../')

import ast
import inspect
from time import sleep
from ..tools.vs_tools import docrule,handle_sast_output
from neotermcolor import cprint,colored as cl

class vs_authorization:
    def __init__(self, **options:dict) -> None:
        self.options = options
        self.object = cl(self.options.get("obj_name",False),'magenta')
        self.object = self.options.get("obj_name")
        self.issues = []
        self.node_tracker = []
        self.nodes_tracker = set()

    def __show_code__(self, source_code:list=False):
        if not source_code:
            source_code = self.options.get('hl_code')

        print()
        print()
        for line in source_code:
            print(line, end='')
        print()

    def improper_permissions(self, node:ast.AST=False) -> bool:
        if not node:
            node = self.options.get('node') 
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == "permission_required":
                    self.__show_code__()
                    rule = docrule(self.issues)
                    self.options['rule'] = rule
                    handle_sast_output(self.options).gen_sarif()
                    return True
        return False

    def insecure_direct_object_references(self, node: ast.AST = False) -> bool:
        if not node:
            node = self.options.get('node')
        if isinstance(node, ast.Call):
            if (isinstance(node.func, ast.Name) and node.func.id == 'get_object_or_404') \
                    or (isinstance(node.func, ast.Attribute) and node.func.attr in ['get','filter']):
                input_validated = False
                input_sanitized = False
                user_authorized = False
                for k in node.keywords:
                    if k.arg == 'pk' and isinstance(k.value, ast.Call) and k.value.func.id == 'int':
                        input_validated = True
                    elif k.arg == 'pk' and isinstance(k.value, ast.Call) and k.value.func.id == 'escape':
                        input_sanitized = True
                    elif k.arg == 'model' and isinstance(k.value, ast.attribute) and k.value.attr == 'objects':
                        user_authorized = True

        for child_node in ast.iter_child_nodes(node):
            if (self.insecure_direct_object_references(child_node)):
                self.__show_code__()
                rule = docrule(self.issues)
                self.options['rule'] = rule
                handle_sast_output(self.options).gen_sarif()
                break

    def insecure_password_storage(self, node=False):
        from ..tools.vs_tools import check_ssl_setup,check_db_connection
        
        if not node:
            node = self.options.get('node')
        if isinstance(node, ast.FunctionDef):
            is_using_make_password = False
            is_using_check_password = False
            is_using_https = False
            is_using_validation = False
            is_using_bcrypt = False
            is_using_scrypt = False
            is_using_django_library = False
            is_properly_handling_ssl = False
            is_properly_handling_db = False
            is_related_to_password_storage = False

            for statement in node.body:
                if isinstance(statement, ast.ImportFrom):
                    if statement.module == "django.contrib.auth.hashers":
                        if any([name.name in ["make_password", "check_password"] for name in statement.names]):
                            is_related_to_password_storage = True
                            break

            if not is_related_to_password_storage:
                for statement in node.body:
                    if isinstance(statement, ast.Expr):
                        if isinstance(statement.value, ast.Call):
                            if isinstance(statement.value.func, ast.Attribute):
                                if statement.value.func.attr in ["set_password", "check_password"]:
                                    is_related_to_password_storage = True
                                    break
            if not is_related_to_password_storage:
                return False

            for statement in node.body:
                if isinstance(statement, ast.Expr):
                    if isinstance(statement.value, ast.Call):
                        if isinstance(statement.value.func, ast.Name):
                            if statement.value.func.id == "make_password":
                                is_using_make_password = True
                            elif statement.value.func.id == "check_password":
                                is_using_check_password = True
                            elif statement.value.func.id == "bcrypt":
                                is_using_bcrypt = True
                            elif statement.value.func.id == "scrypt":
                                is_using_scrypt = True
                if isinstance(statement, ast.If):
                    if_check = [x for x in statement.body if isinstance(x, ast.If)]
                    if if_check:
                        if_check = if_check[0]
                        if if_check.test.func.id == "ssl":
                            is_using_https = True
                            is_properly_handling_ssl,issues = check_ssl_setup(if_check)

                if isinstance(statement, ast.With):
                    if statement.items[0].context_expr.id in ['cursor','connection']:
                        is_using_validation = True
                        is_properly_handling_db,issues = check_db_connection(statement)

            if not all([
                is_using_make_password,
                is_using_check_password,
                is_using_https,
                is_using_validation,
                (is_using_bcrypt or is_using_scrypt),
                is_properly_handling_ssl,
                is_properly_handling_db
                ]):
                
                self.__show_code__()
                rule = docrule(self.issues)
                self.options['rule'] = rule
                handle_sast_output(self.options).gen_sarif()
    
    def __status__(self, test_type):
        status_msg = (f"    → Running {cl(test_type, 'red')} tests against {self.object}...")
        print(status_msg.ljust(os.get_terminal_size().columns - 1), end="\r")
        sleep(0.04)

    def __start_scan__(self):
        [self.__status__(vst) or getattr(self,vst)() \
            for vst in dir(self) if callable(getattr(self, vst)) \
                and not vst.startswith("__")]

