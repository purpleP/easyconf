import json
import sys
import types
from collections import Mapping, namedtuple, deque, Iterable
from itertools import chain, takewhile, dropwhile
from functools import partial
from operator import itemgetter

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


def merge(fst, snd, *other):
    basetype = next((t for t in (Mapping, Iterable) if isinstance(fst, t)), None)
    if not basetype:
        raise ValueError('Can merge only iterables or mappings')
    if not all(isinstance(v, basetype) for v in other):
        raise ValueError('Can merge only values of the same basetype')
    if basetype is Iterable:
        return list(concat(fst, snd, *other))
    else:
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
    by_path_start = groupby(paths, by_start)
    def is_basecase(args):
        path, values = args
        return len(path) == 0
    by_path_start = {
        start: tuple(map(tuple, partition(is_basecase, tuple((path[1:], vs) for path, vs in values))))
        for start, values in by_path_start
    }
    def make_val(key, schema):
        all_values = concat(
            (transform(schema, *values) for _, values in by_path_start[key][0]),
            (make_value(schema, by_path_start[key][1]),) if by_path_start[key][1] else ()
        )
        all_values = tuple(all_values)
        if len(all_values) > 1:
            return merge(*all_values)
        return all_values[0]
    return {
        key: make_val(key, subschema)
        for key, subschema in schema['properties'].items()
        if key in by_path_start
    }


def transform(schema, value, *values):
    if schema['type'] in transformers:
        if values:
            raise ValueError(f'Too many arguments passed {value} {values}')
        return transformers[schema['type']](value)
    if isinstance(schema['items'], dict):
        return [transform(schema['items'], v) for v in (value,) + values]
    return [
        transform(schema, value)
        for schema, value in zip(schema['items'], (value,) + values)
    ]


transformers = {
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
