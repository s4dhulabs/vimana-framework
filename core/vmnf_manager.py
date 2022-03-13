#!/usr/bin/env python3
#from __future__ import print_function
import copy
import importlib
import json
import os
import platform
import random
import re
import string
import sys
import threading
import time
import traceback
from prettytable import PrettyTable
from neotermcolor import colored, cprint
from res.colors import *

from core.vmnf_engine_exceptions import engineExceptions as _ex_
from helpers.vmnf_helpers import VimanaHelp


def handler_filter_id(mod_filter, filter_by):

    mod_by_fmwk_id = {
        0:'django',
        1:'flask',
        3:'generic'
    }

    mod_cat_by_flag = {
        0:'framework',
        1:'library',
        2:'package',
        3:'function'
    }

    mod_type_by_id = {
        0:'tracker',
        1:'fuzzer',
        2:'attack',
        3:'leaker',
        4:'exploit'
    }

    id_items = {
        'type':mod_type_by_id,
        'category': mod_cat_by_flag,
        'framework':mod_by_fmwk_id
    }

    # filter options len
    mtr = len(id_items[filter_by])

    if filter_by == 'type':
        options_msg = "between 0 and {}. Valid types".format(mtr-1)
    elif filter_by == 'category':
        options_msg = "between 0 and {}. Valid categories".format(mtr-1)
    elif filter_by == 'framework':
        options_msg = "between 0 and {}. Valid categories".format(mtr-1)

    if len(mod_filter) == 1:
        try:
            if int(mod_filter) in range(mtr):
                # if filter by id (0-4) pick the right mod by filter type id
                mod_filter = id_items[filter_by][int(mod_filter)]
            else:
                print(VimanaHelp().__doc__)
                print('\n[vmnf:list] {} Id out of range.You must choose {}:\n'.format(filter_by,options_msg))

        except ValueError:
            print("\033c", end="")
            print(VimanaHelp().__doc__)
            print('\n[vmnf:list] Invalid format. The id must be a one-digit integer identifier\n')

    elif mod_filter \
        not in id_items[filter_by].values():
        print("\033c", end="")
        print(VimanaHelp().__doc__)
        print('\n[vmnf:list] Invalid filter Id. You must choose {}:\n'.format(options_msg))
        
        for k,v in id_items[filter_by].items():
            print(' {}: {}'.format(k,v))
        print()
        
        
    return mod_filter


def vmng(**handler_ns):
    # framework debug argument (not available in this version) 
    _vmnf_stats_ = handler_ns.get('_vmnf_stats_')
    vmnf_debug = False

    if not _vmnf_stats_:
        tbl_pool = []
        filter_pool = []
        modules_table = PrettyTable()    
        modules_table.field_names = [
            str(Y_c +   'name'        + D_c), 
            str(Y_c +   'type'        + D_c), 
            str(Y_c +   'category'    + D_c), 
            str(Y_c +   'description' + D_c)
        ]

        modules_table.align = "l"
        modules_table.title = colored(
            "siddhis","blue")

        module_match = False
        found_modules = []
        run_module = False
        search_module_name  = False
        search_module_type  = False
        search_module_category = False
        framework_target = False

        module_info = handler_ns['module_info']
        module_list = handler_ns['module_list']
        module_run  = handler_ns['module_run']
        module_args = handler_ns['module_args']

        # set choosen module name to info and run commands
        if module_run: 
            search_module_name  = module_run.strip().lower()

        elif module_info:
            search_module_name  = module_info.strip().lower()
        elif module_list:
            if handler_ns['type']:
                smt = handler_ns['type'].rstrip().lower()
                search_module_type = handler_filter_id(smt, 'type')
                filter_pool.append('type: ' + search_module_type)
            if handler_ns['category']:
                smc = handler_ns['category'].rstrip().lower()
                search_module_category = handler_filter_id(smc, 'category')
                filter_pool.append('category: ' + search_module_category)
            if handler_ns['framework']:
                smf = handler_ns['framework'].rstrip().lower()
                framework_target = handler_filter_id(smf, 'framework')
                filter_pool.append('framework: ' + framework_target)

        '''In this alpha version we're just searching modules in this way
        with values in module information dict and checking via python
        In future versions, with more plugins maybe it should be better 
        via database query'''
    
        # set full filters search
        all_filters = True if search_module_type \
        and search_module_category \
        and framework_target else False

        # type category filters
        type_cat_filters = True if search_module_type \
        and search_module_category \
        and not framework_target else False

        # only type filter
        type_filter = True if search_module_type \
        and not search_module_category \
        and not framework_target else False

        # only category filter
        cat_filter = True if search_module_category \
        and not search_module_type \
        and not framework_target else False

        # if no filter list all modules
        list_all = True if not framework_target \
            and not all_filters \
            and not type_cat_filters \
            and not type_filter \
            and not cat_filter else False

        # only framework filter
        fmwk_filter = True if framework_target \
        and not all_filters \
        and not type_cat_filters \
        and not type_filter \
        and not cat_filter else False

        # framework and type 
        fmwk_type_filters = True if framework_target \
        and search_module_type else False
    
        # vmnf debug will be part of resource to debug the framework itself in future versions
        # default is False in this version
        if vmnf_debug and vmnf_debug['auto']:
            list_filter_ops = {
	        'All filters': all_filters,
	        'Type and Category': type_cat_filters,
	        'Only type filter': type_filter,
	        'Only category': cat_filter,
	        'No filter': list_all,
	        'Only framework filter': fmwk_filter,
	        'Framework and typo filters': fmwk_type_filters
            }

            for k,v in list_filter_ops.items():
                print(' + {}: {}'.format(k,v))

            print()
    
    current_directory = os.path.dirname(os.path.realpath(__file__))
    modules_dir = ','.join(current_directory.split('/')[:-1]).replace(',','/') 

    found_module = False
    module_stats_types = {}

    for root, directories, files in os.walk('{}/siddhis'.format(modules_dir)):
        module_name = os.path.basename(root)
        relpath = os.path.relpath(root)
        
        for file in files:
            if file and not file.startswith('_') and file[-3:] == ".py":
                module_path = '{}/{}'.format(relpath, file)
                module_path = (module_path.replace('/', '.').replace('\\', '.'))[:-3]
	       
                try:
                    module = __import__(module_path, globals(), 'siddhi', 1)
                    _siddhi_ = (module.siddhi)
		    
                    # module instance information	
                    module_information  = (_siddhi_.module_information)
                    module_type_ = (module_information['Type']).strip().lower()
                    module_name_ = (module_information['Name']).strip().lower()
                    module_category_ = (module_information['Category']).lower()
                    module_framework_ = (module_information['Framework']).rstrip().lower()
                    module_brief_ = (module_information['Brief'])
                    module_arguments_  = (_siddhi_.module_arguments)
                except AttributeError as AEX:
                    if vmnf_debug:
                        _ex_().template_atribute_error(AEX,module_name)
                        continue
                    pass

                #~ statistics about available siddhis types / load info
                if _vmnf_stats_:
                    m_type = module_type_.lower()
                    
                    if m_type in module_stats_types.keys():
                        module_stats_types[m_type] += 1
                    else:
                        module_stats_types[m_type] = 1
                    continue

                #~ module arguments
                if module_args \
                    and module_args.strip().lower() == module_name_:
                    print(module_arguments_)
                    return 

                #~ run module
                if module_run \
                    and module_name_ == search_module_name:

                    try:
                        status_ok = _siddhi_(**handler_ns).start()
                    except KeyboardInterrupt:
                        sys.exit(1)

                    if not status_ok:
                        '''this is not usefull in this version, but will be [control other siddhi aspects]'''
                        pass

                    return True
                
                #~ show module information
                elif module_info \
                    and module_name_ == search_module_name:
		    
                    # Retrieve full module information 
                    print()
                    for k,v in module_information.items():
                        print("  ~ {}: {} ".format(k, v))
                    return

                #~ list modules by type/category/framework
                elif module_list:

                    # listing all modules 
                    if list_all:
                        found_module = True
                        
                    # filter modules by type, category and framework 
                    elif all_filters:
                        if module_type_ == search_module_type \
                            and search_module_category == module_category_ \
                            and framework_target == module_framework_:
                            found_module = True
                    
                    elif fmwk_type_filters:
                        if module_type_ == search_module_type \
                            and framework_target == module_framework_:
                            found_module = True
                    
                    # filter modules by type and category 
                    elif type_cat_filters:
                        if module_type_ == search_module_type \
                            and search_module_category == module_category_:
                            found_module = True

                    # filter modules by type 
                    elif type_filter:
                        if module_type_ == search_module_type:
                            found_module = True
                    
                    # filter modules by category 
                    elif cat_filter:
                        if search_module_category == module_category_:
                            found_module = True

                    # filter modules by framework
                    elif fmwk_filter:
                        if framework_target == module_framework_:
                            found_module = True

                    else:
                        continue
                    
                    if found_module:
                        found_module = False
                        module_match = True
                        
                        if module_name_ not in tbl_pool:
                            tbl_pool.append(module_name_)

                            modules_table.add_row(
                                [
                                    module_name_, 
                                    module_type_, 
                                    module_category_, 
                                    module_brief_
                                ]
                            )

    if _vmnf_stats_:
        return module_stats_types
    
    #if modules_table:
    if module_match:
        print(modules_table)
        return True
    return False

