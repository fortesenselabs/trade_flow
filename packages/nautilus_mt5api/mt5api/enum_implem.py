""" 
    Simple enum implementation
"""


class Enum:
    def __init__(self, *args):
        self.idx2name = {}
        for (idx, name) in enumerate(args):
            setattr(self, name, idx)
            self.idx2name[idx] = name

    def to_str(self, idx):
        return self.idx2name.get(idx, "NOTFOUND")