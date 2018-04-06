import json
import sys
import os
from collections import Mapping, deque, Iterable
from itertools import chain, dropwhile, takewhile, islice, zip_longest
from itertools import groupby as group

from jsonschema import validate
from split import groupby, partition


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
        return list(chain(fst, snd, *other))
    key_values = (
        chain([k], (d[k] for d in (fst, snd) + other if k in d))
        for k in set(chain(fst, snd, *other))
    )
    return {
        k: merge(val, *values) if values else val
        for k, val, *values in key_values
    }


def make_paths(args):
    def key(arg):
        if arg.startswith('-'):
            key.key = arg
            return arg
        return key.key
    key.key = None
    return tuple(
        (path.strip('--').split('.'), tuple(values))
        for path, (_, *values) in group(args, key)
        if path is not None and path.startswith('--conf')
    )


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
        all_values = chain(
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
        properties = chain(properties, additional_properties)
    return {key: value for key, value in properties}


def transform(schema, values):
    trans = transformers.get(schema['type'])
    if trans:
        return trans(*values)
    if isinstance(schema['items'], dict):
        if schema['items']['type'] == 'object' and len(values) == 1:
            return json.loads(values[0])
        return [transform(schema['items'], v) for v in values]
    return [
        transform(schema, value)
        for schema, value in zip(schema['items'], values)
    ]

def json_from_string_or_file(string_or_file_path):
    try:
        return json.loads(string_or_file_path)
    except json.JSONDecodeError:
        with open(string_or_file_path, 'r') as f:
            return json.load(f)


transformers = {
    'integer': int,
    'number': float,
    'boolean': lambda *args: True,
    'string': str,
    'object': json_from_string_or_file,
    'array': json_from_string_or_file,
}
