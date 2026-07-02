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
from neotermcolor import colored
from prettytable import PrettyTable


def get_specs():
    return VFDBOps().list_resource('_SPECS_', [])


def list_specs(specs=None):
    if specs is None:
        specs = get_specs()

    if not specs:
        print(colored('No API specs found.', 'yellow'))
        print()
        return False

    output_table = PrettyTable()
    output_table.title = f"Vimana API Specs - {len(specs)} registered"
    output_table.field_names = [
        "Index", "ID", "Title", "FastAPI", "OpenAPI",
        "Host", "Paths", "Methods", "Date",
    ]
    output_table.align = 'l'

    for tbl_index, spec in enumerate(specs, 1):
        output_table.add_row([
            tbl_index,
            colored(spec.spec_id, 49),
            spec.spec_title[:20] if spec.spec_title else '',
            spec.fastapi_version,
            spec.openapi_version,
            spec.spec_host,
            spec.spec_paths,
            spec.spec_methods,
            spec.spec_date,
        ])

    print(output_table)
    print()
    return specs


class VFSpecsManager:
    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.model = '_SPECS_'

    def get_specs(self):
        return VFDBOps().list_resource(self.model, [])

    def list_specs(self):
        return list_specs(self.get_specs())
