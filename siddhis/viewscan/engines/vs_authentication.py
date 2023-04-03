import os
import sys

sys.path.append('../')

import ast
import inspect
from time import sleep
from neotermcolor import cprint,colored as cl
from ..tools.vs_tools import check_match,is_validate_password_call_without_password,docrule,handle_sast_output

class vs_authentication:
    def __init__(self, **options:dict) -> None:
        self.options = options
        self.object = self.options["obj_name"]
        self.issues = []

    def __show_code__(self, source_code:list=False):
        if not source_code:
            source_code = self.options.get('hl_code')

        print()
        print()
        for line in source_code:
            print(line, end='')
        print()

    def login_required_issues(self, node:ast.AST=False) -> bool:
        issues = []
        if not node:
            node = self.options.get('node')
        if isinstance(node, ast.FunctionDef) \
                and (check_match('login_required', self.options['dec_args']) \
            or 'login_required' in self.options['node_decorators']):

            if 'request' not in [arg.arg for arg in node.args.args]:
                issues.append(f"Missing request object checks")
            else:
                check_auth = False
                for stmt in node.body:
                    if isinstance(stmt, ast.If):
                        if 'request.user.is_authenticated' in ast.dump(stmt):
                            check_auth = True
                            break
                if not check_auth:
                    issues.append(f"Missing request.user.is_authenticated checks")

        if issues:
            self.__show_code__()
            rule = docrule(self.issues)
            self.options['rule'] = rule
            handle_sast_output(self.options).gen_sarif()
            return True
        return False
    
    def csrf_exempt(self, node:ast.AST=False) -> bool:
        if 'csrf_exempt' in self.options['node_decorators']:
            self.__show_code__()
            rule = docrule(self.issues)
            self.options['rule'] = rule
            handle_sast_output(self.options).gen_sarif()
            return True
        return False
            
    def unchecked_redirects(self, node:ast.AST=False) -> bool:
        if not node:
            node = self.options.get('node')
        if isinstance(node, ast.Return) \
            and isinstance(node.value, ast.Call) \
            and isinstance(node.value.func, ast.Name) \
            and node.value.func.id == 'HttpResponseRedirect':
            
            if not any(keyword.arg == 'next' for keyword in node.value.keywords):
                self.__show_code__()
                rule = docrule(self.issues)
                self.options['rule'] = rule
                handle_sast_output(self.options).gen_sarif()
                return True
        elif isinstance(node, ast.FunctionDef):
            for stmt in node.body:
                self.unchecked_redirects(stmt)

    def user_objects_create_user(self, node:ast.AST=False) -> bool:
        if not node:
            node = self.options.get('node')
        user_type = False
        issues = []

        for stmt in node.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                if hasattr(stmt.value.func, 'attr') and stmt.value.func.attr == 'create_superuser':
                    user_type = 'superuser'
                elif hasattr(stmt.value.func, 'attr') and stmt.value.func.attr == 'create_user':
                    user_type = 'user'
                if user_type and not any(keyword.arg == 'password' for keyword in stmt.value.keywords):
                    issues.append(f'using User.objects.create_{user_type} without setting password')
        if issues:
            self.__show_code__()
            rule = docrule(self.issues)
            self.options['rule'] = rule
            handle_sast_output(self.options).gen_sarif()
            return True
        return False
            
    def password_plaintext(self, node:ast.AST=False) -> bool:
        if not node:
            node = self.options.get('node')
        if isinstance(node, ast.FunctionDef):
            for stmt in node.body:
                if isinstance(stmt, ast.Return):
                    if isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name) \
                        and stmt.value.func.id == 'check_password':
                        self.issues.append(True)
                elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) \
                    and isinstance(stmt.value.func, ast.Name) \
                    and stmt.value.func.id == 'check_password':
                    self.issues.append(True)
        elif isinstance(node, ast.Module) and any(
            self.password_plaintext(stmt)
                for stmt in node.body
            ):
                self.issues.append(True)

        if self.issues:
            self.__show_code__()
            rule = docrule(self.issues)
            self.options['rule'] = rule
            handle_sast_output(self.options).gen_sarif()
            return True
        return False

    def set_password_plaintext(self, node:ast.AST=False) -> bool:
        if not node:
            node = self.options.get('node')
        for stmt in node.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                if isinstance(stmt.value.func, ast.Attribute):
                    if stmt.value.func.attr == 'set_password':
                        self.__show_code__()
                        rule = docrule(self.issues)
                        self.options['rule'] = rule
                        handle_sast_output(self.options).gen_sarif()
                        return True
        return False

    def auth_login_next(self, node=False):
        has_next_param = False
        if not node:
            node = self.options.get('node')
        if isinstance(node, ast.FunctionDef):
            for stmt in node.body:
                self.auth_login_next(stmt)
        elif isinstance(node, ast.ClassDef):
            for stmt in node.body:
                self.auth_login_next(stmt)
        elif isinstance(node, ast.If):
            for stmt in node.body:
                self.auth_login_next(stmt)
            for stmt in node.orelse:
                self.auth_login_next(stmt)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            try:
                func_name = node.value.func.id
            except AttributeError:
                return False

            if func_name == 'login':
                has_next_param = False
                for keyword in node.value.keywords:
                    if keyword.arg == 'next':
                        has_next_param = True
                        break

                if not has_next_param:
                    self.__show_code__()
                    rule = docrule(self.issues)
                    self.options['rule'] = rule
                    handle_sast_output(self.options).gen_sarif()
                    return True
        return False

    def password_validation_user(self, node:ast.AST=False) -> bool:
        found_validate_password = False
        if not node:
            node = self.options.get('node')
        issue_found = False
        def is_validate_password_call_without_user(node):
            return (isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'validate_password' and
                    node.func.value.id == 'password_validation' and
                    'user' not in node.keywords)

        if isinstance(node, ast.FunctionDef):
            for stmt in node.body:
                if isinstance(stmt, ast.Try):
                    for sub_stmt in stmt.body:
                        if isinstance(sub_stmt, ast.Expr) and is_validate_password_call_without_user(sub_stmt.value):
                            issue_found = True
                elif isinstance(stmt, ast.Expr):
                    if is_validate_password_call_without_user(stmt.value):
                        issue_found = True
        if issue_found:
            self.__show_code__()
            rule = docrule(self.issues)
            self.options['rule'] = rule
            handle_sast_output(self.options).gen_sarif()
            return True

    def authenticate_hardcoded_password(self, node:ast.AST=False, _done_:bool=True) -> bool:
        if not node:
            node = self.options.get('node')
        for child_node in ast.iter_child_nodes(node):
            if isinstance(child_node, ast.Call):
                if isinstance(child_node.func, ast.Attribute) and child_node.func.attr == "authenticate":
                    for keyword in child_node.keywords:
                        if keyword.arg == "password" and isinstance(keyword.value, ast.Str):
                            self.__show_code__()
                            rule = docrule(self.issues)
                            self.options['rule'] = rule
                            handle_sast_output(self.options).gen_sarif()
                            return True
            self.authenticate_hardcoded_password(child_node, False)

        if _done_:
            return False

    def password_validation_password(self, node:ast.AST=False) -> bool:
        found_validate_password = False
        if not node:
            node = self.options.get('node')
        issue_found = False

        if isinstance(node, ast.FunctionDef):
            for stmt in node.body:
                if isinstance(stmt, ast.Try):
                    for sub_stmt in stmt.body:
                        if isinstance(sub_stmt, ast.Expr) \
                                and is_validate_password_call_without_password(sub_stmt.value):
                            issue_found = True
                elif isinstance(stmt, ast.Expr):
                    if is_validate_password_call_without_password(stmt.value):
                        issue_found = True
        if issue_found:
            self.__show_code__()
            rule = docrule(self.issues)
            self.options['rule'] = rule
            handle_sast_output(self.options).gen_sarif()
            return True
        return False

    def __status__(self, test_type):
        status_msg = (f"    → Running {cl(test_type, 'red')} tests against {self.object}...")
        print(status_msg.ljust(os.get_terminal_size().columns - 1), end="\r")
        sleep(0.04)

    def __start_scan__(self):
        [self.__status__(vst) or getattr(self,vst)() \
            for vst in dir(self) if callable(getattr(self, vst)) \
                and not vst.startswith("__")]

