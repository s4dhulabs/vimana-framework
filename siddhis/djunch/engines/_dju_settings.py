

class table_models:
    def __init__(self):
        self.exception_tbl_set = {
            'fields': [
                'iid', 
                'type', 
                'function', 
                'location', 
                'line', 
                'lines', 
                'triggers', 
                'env', 
                'vars', 
                'occurrences'
            ],
            'title' : 'Exceptions',
            'color' : 'blue',
            'attrs' : ['bold'],
            'align' : 'c' 
        }    
        self.config_tbl_set = {
            'fields': ['iid', 'status', 'method', 'issue'],
            'title' : 'Configuration Issues',
            'color' : 'blue',
            'attrs' : ['bold'],
            'align' : 'c' 
        }
        self.summary_tbl_set = {
            'fields': ['Issues', 'Security Tickets', "CVE's"],
            'title' : 'Security Tickets',
            'color' : 'blue',
            'attrs' : ['bold'],
            'align' : 'c' 
        }
        self.tickets_tbl_set = {
            'fields': ['iid', 'title'],
            'title' : 'Security Tickets',
            'color' : 'blue',
            'attrs' : ['bold'],
            'align' : 'c' 
        }
        self.envleak_tbl_set = {
            'fields': ['iid', 'context', 'variables'],
            'title' : 'Environmet Contexts',
            'color' : 'blue',
            'attrs' : ['bold'],
            'align' : 'c' 
        }
        self.cves_tbl_set = {
            'fields': ['iid', 'title', 'date'],
            'title' : 'CVEs',
            'color' : 'blue',
            'attrs' : ['bold'],
            'align' : 'c' 
        }
        self.traceback_tbl_set = {
            'fields': ['Variable', 'Object', 'Address'],
            'title' : 'Django Traceback Objects',
            'color' : 'blue',
            'attrs' : ['bold'],
            'align' : 'c' 
        }
        self.siddhis_tbl_set = {
            'fields': ['Name', 'Type', 'Category', 'Info'],
            'title' : 'siddhis',
            'color' : 'yellow',
            'attrs' : ['bold'],
            'align' : 'l' 
        }
        self.sttinger_findings_set = {
            'fields': ['Endpoint', 'Version', 'Vrange', 'CVEs', 'Tickets'],
            'title' : 'Sttinger Fingerprint',
            'color' : 'yellow',
            'attrs' : ['bold'],
            'align' : 'l' 
        }



