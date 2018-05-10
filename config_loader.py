import sys


class CustomLoader:
    name = 'conf'

    def find_module(self, fullname, path):
        return self if fullname == self.name else None

    def load_module(self, fullname):
        module = sys.modules.get(fullname)
        if module:
            return module
        if fullname != self.name:
            raise ImportError(fullname)
        sys.modules[fullname] = Dict()
        return sys.modules[fullname]


class Dict(dict):
    def __getattr__(self, attr):
        try:
            return self[attr]
        except:
            raise AttributeError(attr)
