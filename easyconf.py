import json
import sys
import types
import os
from collections import Mapping, deque, Iterable
from itertools import chain, takewhile

from jsonschema import validate
from more_functools import concat
from split import groupby, partition


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


def find_conf_schema():
    script_dir = sys.path[0]
    if script_dir == '':
        raise Exception('Can\'t find conf_schema when sys.path == ""')
    with open(os.path.join(script_dir, 'conf_schema.json'), 'r') as schema:
        return json.load(schema)


def parse_args(conf_schema=None):
    conf_schema = conf_schema or find_conf_schema()
    schema = {'type': 'object', 'properties': {'conf': conf_schema}}
    config = make_value(schema, make_paths(sys.argv))['conf']
    validate(config, conf_schema)
    import conf
    conf.conf = config
    return config


def merge(fst, snd, *other):
    basetype = next((t for t in (Mapping, Iterable) if isinstance(fst, t)), None)
    if not basetype:
        raise ValueError('Can merge only iterables or mappings')
    elif not all(isinstance(v, basetype) for v in other):
        raise ValueError('Can merge only values of the same basetype')
    elif basetype is Iterable:
        return list(concat(fst, snd, *other))
    key_values = (
        concat([k], (d[k] for d in (fst, snd) + other if k in d))
        for k in set(chain(fst, snd, *other))
    )
    return {
        k: merge(val, *values) if values else val
        for k, val, *values in key_values
    }


def make_paths(args):
    def is_not_argname(arg):
        return not arg.startswith('--')
    iargs = Buffered(args, 1)
    for arg in iargs:
        if is_not_argname(arg):
            continue
        yield arg.strip('--').split('.'), list(takewhile(is_not_argname, iargs))
        iargs.from_buffer = True

def make_value(schema, paths):
    def by_start(args):
        path, values = args
        return path[0]
    def is_basecase(args):
        path, values = args
        return len(path) == 0
    by_path_start = {
        start: tuple(map(tuple, partition(is_basecase, ((path[1:], vs) for path, vs in values))))
        for start, values in groupby(paths, by_start)
    }
    def make_val(key, schema):
        basecases, nonbasecases = by_path_start[key]
        all_values = concat(
            (transform(schema, values) for _, values in basecases),
            (make_value(schema, by_path_start[key][1]),) if nonbasecases else ()
        )
        all_values = tuple(all_values)
        if len(all_values) > 1:
            return merge(*all_values)
        return all_values[0]
    props = schema.get('properties', {})
    properties = (
        (key, make_val(key, subschema))
        for key, subschema in props.items()
        if key in by_path_start
    )
    additional_props = schema.get('additionalPoperties', False)
    if additional_props:
        additional_properties = (
            (key, make_val(key, additional_props))
            for key in by_path_start.keys() - props.keys()
        )
        propeties = concat(properties, additional_props)
    return {key: value for key, value in properties}



def transform(schema, values):
    if schema['type'] in transformers:
        if len(values) > 1:
            raise ValueError(f'Too many arguments passed {values}')
        return transformers[schema['type']](*values)
    if isinstance(schema['items'], dict):
        if schema['items']['type'] == 'object' and len(values) == 1:
            return json.loads(values[0])
        return [transform(schema['items'], v) for v in values]
    return [
        transform(schema, value)
        for schema, value in zip(schema['items'], values)
    ]


transformers = {
    'integer': int,
    'number': float,
    'boolean': lambda *args: True,
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
