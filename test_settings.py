import yaml
import os

d={
    'project': {
        'name': 'Vimana Framework',
        'version': 'v0.8',
        'tag': 'alpha',
        'git': 'https://github.com/s4dhulabs/vimana-framework',
        'author': "s4dhu",
        'email': "<s4dhul4bs[at]prontonmail.ch>",
        'site': 'https://s4dhulabs.github.io/'
    },
    'settings': {
        'utils': {
            'random_headers': 'res/random_headers.yaml'
        },
        'sessions': 'core/sessions/',
        'siddhis_set': {
            'dir': 'siddhis/',
            'list': [s for s in os.listdir('siddhis') \
                if not s.startswith('__') and not s.endswith('.yaml')
            ]
        },
        'case_set': {
            'cases_path': 'core/cases/',
            'cases_yf':'core/cases/*.yaml',
            'empty_msg':"""[{}] It seems like you didn\'t create any case yet, or they were flushed."""
        },
        'arg_parser': {
            'require_args': [
                '--save-case',
                '--target',
                '--file',
                '--ip-range',
                '--cidr-range',
                '--target-list',
                '--port',
                '--port-list',
                '--port-range',
                '--fuzzer',
                '--proxy',
                '--proxy-type',
                '--nmap-xml',
                '--abduct',
                '--module',
                '--session',
                '--target-url',
                '--project-dir',
                '--target-dir',
                '--project',
                '--use-request',
                '--plugin',
                '--case',
                '--data',
                '--form-input-target',
                '--target-input',
                '--django-version',
                '--inspect',
                '--methods',
                '--method',
                '--fuzzspecs',
                '--fuzzspec',
                '-m',
                '--flush-spec',
                '--set-path',
                '--custom-variations',
                '--set-parameter',
                '--set-param'
            ]

        }

    }
}

file_path='core/vmnf_settings.yaml'
with open(file_path, 'w+') as file:
    yaml.dump(d, file, indent=4, sort_keys=True)

