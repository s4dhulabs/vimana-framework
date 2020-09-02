from resources import colors


# PrintIt._step_('parse_urlconf')

class StepHandler:
    def __init__(self, value, step):
        
        self.step  = step
        self.value = colors.Y_c  + value + colors.D_c 
        self.flag  = colors.Gn_c + "⠿⠥" + colors.D_c

    def _step_(self):
    
        if self.step == 'port_state_validate':
            msg = "Validating port state for target {}...".format(
                self.value
            )

        elif self.step == 'parse_urlconf':
            msg = "Parsing fuzzer scope via URLconf: {}...".format(
                self.value
            )

        elif self.step == 'parse_patterns_file':
            msg = "Parsing fuzzer scope via patterns file: {}...".format(
                self.value


        print("{} {}\n".format(
            self.flag,
            self.msg
            )
        )

