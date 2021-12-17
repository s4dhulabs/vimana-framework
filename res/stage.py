import yaml
import res.vmnf_validators as val

class stager:
    def __init__(self,**session):
        self.session = session
        self.stage = 'siddhis/stage.yaml'

    def forward_session(self):
        with open(self.stage, 'w') as file:
            yaml.dump(self.session, 
                file,default_flow_style=False)

    def check_forward(self):
        if not val.check_file(self.stage):
            return False
        
        with open(self.stage) as file:
            sts = yaml.load(file, 
                Loader=yaml.FullLoader)
        return sts
