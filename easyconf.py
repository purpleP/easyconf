import json
import sys
import types
from argparse import ArgumentParser
from collections import Mapping, namedtuple, deque
from itertools import chain, takewhile
from functools import partial

from jsonschema import validate
from more_functools import merge


class Buffered:
    def __init__(self, sequence, size=1):
        self.buffer = deque(maxlen=size)
        self.sequence = iter(sequence)
        self.from_buffer = False
        self.ended = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.from_buffer:
            try:
                return self.buffer.popleft()
            except IndexError:
                if self.ended:
                    raise StopIteration()
                else:
                    self.from_buffer = False
                    return next(self)
        try:
            elem = next(self.sequence)
            self.buffer.append(elem)
            return elem
        except StopIteration:
            self.ended = True
            raise

def group_by_argname(args):
    iargs = Buffered(args, 1)
    for arg in iargs:
        if arg.startswith('--conf.'):
            yield arg[7:], takewhile(lambda a: not a.startswith('--conf'), iargs)
            iargs.from_buffer = True


def make_dict(schema, args):
    groups = group_by_argname(args)
    return {
        key: make_value(key, subschema, groups)
        for key, subschema in schema['properties'].items()
    }


def make_value(key, schema, groups):
    groups_for_key = tuple(
        (argname, values)
        for argname, values if argname.startswith(key + '.') == key
    )


# def paths_from_namespace(namespace_dict):
#     return (
#         (k.split('.'), v)
#         for k, v in namespace_dict.items() if v is not None
#     )


# def namespace_to_dict(namespace):
#     namespace_dict = vars(namespace)
#     defaults = namespace_dict.pop('conf') or {}
#     conf = dict_from_paths(*paths_from_namespace(namespace_dict))['conf']
#     return merge(defaults, conf)


# def dict_from_paths(*paths):
#     def new_path(path):
#         (key, *rest), value = path
#         return rest, value
#     if len(paths) == 1 and len(paths[0][0]) == 0:
#         return paths[0][1]
#     return {
#         key: dict_from_paths(*map(new_path, remaining_paths))
#         for key, remaining_paths in groupby(paths, lambda ks: ks[0][0])
#     }


# def chain_path(key, path):
#     return chain((key,), path[0]), path[1]


# def paths_from_dict(dct):
#     def make_path(k, v):
#         if isinstance(v, Mapping):
#             map(partial(chain_path, k), paths_frm_dict(v))
#         else:
#             ((key,), v)
#     return (make_path(k, v) for k, v in dct.items())


# def make_argparser(schema):
#     parser = ArgumentParser(description=schema.get('description', ''))
#     for kwargs in schema_to_kwargs(schema, name='conf'):
#         name = kwargs.pop('name')
#         parser.add_argument(name, **kwargs)
#     return parser


# def schema_to_kwargs(schema, name):
#     kwargs = {**common_kwargs(schema, name), **specific_kwargs(schema)}
#     flattened_dict_args = ()
#     if schema['type'] == 'object':
#         flattened_dict_args = chain.from_iterable(
#             schema_to_kwargs(pschema, '.'.join((name, pname)))
#             for pname, pschema in schema['properties'].items()
#         )
#     return chain((kwargs,), flattened_dict_args)


# def specific_kwargs(schema):
#     kwargs = {}
#     type = schema['type']
#     if type == 'array':
#         if len(schema['items']) > 1:
#             raise Exception(
#                 'Easyconf doesn\'t support array with tuple validation.\n{}'.format(schema)
#             )
#         kwargs['type'] = jsonschema_types[schema['items'][0]['type']]
#         kwargs['nargs'] = '+'
#     elif type == 'object':
#         kwargs['type'] = json.loads
#     elif type == 'boolean':
#         kwargs['action'] = 'store_true'
#     else:
#         kwargs['type'] = jsonschema_types[type]
#     return kwargs


# def common_kwargs(schema, name):
#     result = dict(
#         name='--' + name,
#         help=schema.get('description', ''),
#     )
#     return result


jsonschema_types = {
    'integer': int,
    'number': float,
    'boolean': bool,
    'string': str,
    'object': json.loads,
}


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
        sys.modules[fullname] = ConfigModule(None)
        return sys.modules[fullname]

class ConfigModule(types.ModuleType):
    def __init__(self, conf=None):
        self.conf = conf
