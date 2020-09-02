


def get_tool_scope(**args):

    siddhi_args = args
    targets_ports_set = []
    targets = []
    ports = []

    # ignore-state enabled: all targets and ports are going to be tested
    if 'targets' in siddhi_args['scope']:
        
        # get targets
        if siddhi_args['scope']['targets']:
            for target in siddhi_args['scope']['targets']:
                if target not in targets:
                    targets.append(target.strip())
            
        # get ports
        if siddhi_args['scope']['ports']:
            for port in siddhi_args['scope']['ports']:
                if port not in ports:
                    ports.append(port.strip())
        else:
            print('[djonga: {}] Missing target scope'.format(datetime.now()))
            return False

    # ignore-state disabled: port arguments were tested
    else:
        for k,v in siddhi_args['scope'].items():
            for target in list(v):
                if target not in targets_ports_set:
                    targets_ports_set.append(target.strip())

    # final scope object
    if not targets_ports_set:
        if targets and ports:
            for target in targets:
                for port in ports:
                    targets_ports_set.append('{}:{}'.format(
                        target.strip(),
                        port.strip()
                        )
                    )

    return targets_ports_set

