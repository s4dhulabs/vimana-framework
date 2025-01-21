import cmd
import readline
import json
import getpass
from tabulate import tabulate
import pygments
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
from colorama import init, Fore, Style

from res.vmnf_banners import case_header

# Inicializa o colorama
init(autoreset=True)

class EnvCLI(cmd.Cmd):
    case_header()
    #intro = f"{Fore.CYAN}\nWelcome to the Environment CLI. Type 'help' or 'options' to list commands.{Style.RESET_ALL}\n"
    prompt = '>> '

    # Lista de comandos disponíveis com descrição
    commands = {
        'add_var': 'Add a new variable: add_var <name> <value>',
        'add_vars': 'Add multiple variables: add_vars <name1> <name2> ...',
        'set_env': 'Set or modify the environment name: set_env <name>',
        'load_vars': 'Load variables from a JSON file: load_var <file.json>',
        'list_vars': 'List all variables in JSON format or as a table: list_vars [--table]',
        'list_envs': 'List all existing environments (to be implemented)',
        'modify_var': 'Modify a variable: modify_var <old_name> <new_name> <new_value>',
        'delete_var': 'Delete a variable: delete_var <name>',
        'delete_env': 'Delete the current environment',
        'reset': 'Reset the current session (clear all variables and environment)',
        'save': 'Save the environment and variables and display a JSON summary',
        'export_env': 'Export the current environment to a JSON file: export_env [<file.json>]',
        'exit': 'Exit the terminal',
        'help': 'Alias for help',
        'options': 'Alias for help'
    }

    def __init__(self):
        super().__init__()
        self.variables = []
        self.env_name = ""
        self.username = getpass.getuser()
        self.update_prompt()

    # Atualiza o prompt com o nome do usuário e do ambiente
    def update_prompt(self):
        env_display = self.env_name if self.env_name else 'set_env'
        self.prompt = f"{Fore.GREEN}{self.username}@{env_display} >> {Style.RESET_ALL}"

    # Função de autocompletar para comandos
    def completenames(self, text, *ignored):
        """Função para sugerir comandos disponíveis ao pressionar Tab"""
        return [cmd for cmd in self.commands if cmd.startswith(text)]

    # Função para realçar JSON com Pygments
    def highlight_json(self, data):
        json_str = json.dumps(data, indent=4)
        return highlight(json_str, JsonLexer(), TerminalFormatter())

    # Validação para verificar se a variável existe
    def variable_exists(self, var_name):
        return any(var_name == vn for vn, vv in self.variables)

    # Comando para definir ou modificar o nome do ambiente
    def do_set_env(self, line):
        "Set or modify the environment name: set_env <name>"
        if line:
            self.env_name = line
            self.update_prompt()
            print(f"{Fore.YELLOW}Environment name set to '{self.env_name}'{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}You must provide a name for the environment.{Style.RESET_ALL}")

    # Comando para adicionar uma variável manualmente
    def do_add_var(self, line):
        "Add a variable: add_var <name> <value>"
        try:
            var_name, var_value = line.split()
            self.variables.append((var_name, var_value))
            print(f"{Fore.YELLOW}Variable '{var_name}' added with value '{var_value}'{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Usage: add_var <name> <value>{Style.RESET_ALL}")

    # Comando para adicionar múltiplas variáveis
    def do_add_vars(self, line):
        "Add multiple variables: add_vars <name1> <name2> ..."
        if not line.strip():
            print(f"{Fore.RED}Please provide at least one variable name.{Style.RESET_ALL}")
            return
        var_names = [name.strip() for name in line.replace(",", " ").split()]
        for var_name in var_names:
            if var_name:
                var_value = input(f"Enter value for '{var_name}': ")
                self.variables.append((var_name, var_value))
                print(f"{Fore.YELLOW}Variable '{var_name}' added with value '{var_value}'{Style.RESET_ALL}")

    # Comando para carregar variáveis de um arquivo JSON
    def do_load_var(self, line):
        "Load variables from a JSON file: load_var <file.json>"
        if not line.strip():
            print(f"{Fore.RED}Please provide a JSON file path.{Style.RESET_ALL}")
            return
        try:
            with open(line, 'r') as f:
                json_vars = json.load(f)
                for var_name, var_value in json_vars.items():
                    self.variables.append((var_name, var_value))
            print(f"{Fore.YELLOW}Loaded {len(json_vars)} variables from '{line}'{Style.RESET_ALL}")
        except FileNotFoundError:
            print(f"{Fore.RED}File '{line}' not found.{Style.RESET_ALL}")
        except json.JSONDecodeError:
            print(f"{Fore.RED}Invalid JSON format in '{line}'.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error loading JSON file: {e}{Style.RESET_ALL}")

    # Exibir as variáveis atuais em JSON ou tabela
    def do_list_vars(self, line):
        "List all variables in JSON format or as a table: list_vars [--table]"
        if self.variables:
            if '--table' in line:
                table_data = [[var_name, var_value] for var_name, var_value in self.variables]
                print(f"\n{Fore.MAGENTA}Environment: {self.env_name if self.env_name else 'set_env'}{Style.RESET_ALL}")
                print(tabulate(table_data, headers=[f"{Fore.GREEN}Variable{Style.RESET_ALL}", f"{Fore.GREEN}Value{Style.RESET_ALL}"], tablefmt="grid"))
            else:
                vars_dict = {var_name: var_value for var_name, var_value in self.variables}
                print(self.highlight_json(vars_dict))
        else:
            print(f"{Fore.RED}No variables added yet.{Style.RESET_ALL}")

    # Comando para listar ambientes (placeholder para implementação futura)
    def do_list_envs(self, line):
        "List all existing environments (to be implemented)"
        print(f"{Fore.CYAN}This feature will list environments from the database (to be implemented).{Style.RESET_ALL}")

    # Comando para modificar uma variável existente
    def do_modify_var(self, line):
        "Modify a variable: modify_var <old_name> <new_name> <new_value>"
        try:
            old_name, new_name, new_value = line.split()
            if not self.variable_exists(old_name):
                print(f"{Fore.RED}Variable '{old_name}' not found.{Style.RESET_ALL}")
                return
            for i, (var_name, var_value) in enumerate(self.variables):
                if var_name == old_name:
                    self.variables[i] = (new_name, new_value)
                    print(f"{Fore.YELLOW}Variable '{old_name}' modified to '{new_name}' with value '{new_value}'{Style.RESET_ALL}")
                    break
        except ValueError:
            print(f"{Fore.RED}Invalid input. Usage: modify_var <old_name> <new_name> <new_value>{Style.RESET_ALL}")

    # Comando para excluir uma variável
    def do_delete_var(self, line):
        "Delete a variable: delete_var <name>"
        var_name = line.strip()
        if not var_name:
            print(f"{Fore.RED}Please provide a variable name.{Style.RESET_ALL}")
            return
        if not self.variable_exists(var_name):
            print(f"{Fore.RED}Variable '{var_name}' not found.{Style.RESET_ALL}")
            return
        self.variables = [(vn, vv) for vn, vv in self.variables if vn != var_name]
        print(f"{Fore.YELLOW}Variable '{var_name}' deleted.{Style.RESET_ALL}")

    # Comando para excluir o ambiente atual
    def do_delete_env(self, line):
        "Delete the current environment"
        if self.env_name:
            confirm = input(f"Are you sure you want to delete environment '{self.env_name}'? (y/n): ").lower()
            if confirm == 'y':
                self.env_name = ""
                self.variables = []
                self.update_prompt()
                print(f"{Fore.YELLOW}Environment deleted.{Style.RESET_ALL}")
            else:
                print(f"{Fore.CYAN}Environment deletion cancelled.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}No environment set to delete.{Style.RESET_ALL}")

    # Comando para exportar o ambiente para um arquivo JSON
    def do_export_env(self, line):
        "Export the current environment to a JSON file: export_env [<file.json>]"
        if not self.env_name:
            print(f"{Fore.RED}Please set the environment name with 'set_env' first.{Style.RESET_ALL}")
            return

        # Usar o nome do ambiente como nome do arquivo, caso não seja fornecido
        file_name = line.strip() if line.strip() else f"{self.env_name}_env.json"

        env_data = {
            "environment_name": self.env_name,
            "variables": {var_name: var_value for var_name, var_value in self.variables}
        }

        try:
            with open(file_name, 'w') as f:
                json.dump(env_data, f, indent=4)
            print(f"{Fore.YELLOW}Environment exported successfully to '{file_name}'{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error exporting environment: {e}{Style.RESET_ALL}")

    # Comando para salvar as variáveis e exibir o JSON final
    def do_save(self, line):
        "Save the environment and variables and display a JSON summary"
        if not self.env_name:
            print(f"{Fore.RED}Please set the environment name with 'set_env' first.{Style.RESET_ALL}")
            return

        env_data = {
            "environment_name": self.env_name,
            "variables": {var_name: var_value for var_name, var_value in self.variables}
        }

        # Exibir o JSON com sintaxe destacada
        print("\nEnvironment JSON Summary:")
        print(self.highlight_json(env_data))

    # Comando de reset
    def do_reset(self, line):
        "Reset the current session (clear all variables and environment)"
        self.env_name = ""
        self.variables = []
        self.update_prompt()
        print(f"{Fore.YELLOW}Session reset. All variables and environment cleared.{Style.RESET_ALL}")

    # Comando de help detalhado com mais espaçamento e cores
    def do_help(self, arg):
        if arg:
            # Exibe o help específico para o comando se solicitado
            if arg in self.commands:
                print(f"{Fore.GREEN}{arg}: {self.commands[arg]}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}No help found for '{arg}'{Style.RESET_ALL}")
        else:
            # Exibe todos os comandos com descrições
            print()
            print(f"\n{Fore.GREEN}Commands:{Style.RESET_ALL}")
            print()
            for cmd, description in self.commands.items():
                print(f"{Fore.GREEN}{cmd:<12}{Style.RESET_ALL} {description}")
            print()

    # Alias para help
    def do_he(self, arg):
        "Alias for help"
        self.do_help(arg)

    def do_options(self, arg):
        "Alias for help"
        self.do_help(arg)

    # Comando para sair do terminal interativo
    def do_exit(self, line):
        "Exit the terminal"
        print(f"{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
        return True

    # Interrupção limpa com Ctrl-C
    def cmdloop(self, intro=None):
        try:
            super().cmdloop(intro)
        except KeyboardInterrupt:
            print(f"\n{Fore.CYAN}Session interrupted. Type 'exit' to quit gracefully.{Style.RESET_ALL}")
            self.cmdloop()

    # Override do método para evitar reutilização do último comando ao pressionar Enter
    def emptyline(self):
        self.do_help(None)

    # Método para iniciar o programa
    def start(self):
        # Configurar o autocompletar no terminal
        readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind('tab: complete')

        self.cmdloop()

if __name__ == '__main__':
    cli = EnvCLI()
    cli.start()
