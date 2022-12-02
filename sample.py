from dataclasses import dataclass

@dataclass
class Sample():
    '''
    training examples
    '''
    url: str
    targets: dict

    def get_url(self):
        return self.url
    
    def get_targets(self):
        return self.targets
