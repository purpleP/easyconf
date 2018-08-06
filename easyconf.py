import json
import sys
import os

from collections import deque
from itertools import chain, dropwhile, takewhile, islice, zip_longest
from itertools import groupby as group
from operator import itemgetter

from jsonschema import validate
from split import groupby, partition

from config_loader import Dict


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
    def to_Dict(v):
        if isinstance(v, dict):
            return Dict((k, to_Dict(v)) for k, v in v.items())
        elif isinstance(v, list):
            return [*map(to_Dict, v)]
        else:
            return v
    conf.update(to_Dict(config))
    return config


def merge(fst, snd=None, *other):
    if not snd:
        return fst
    fst_type = type(fst)
    if not all(type(arg) == fst_type for arg in (snd, *other)):
        raise ValueError('Can merge only values of the same basetype')
    if fst_type == list:
        return list(chain(fst, snd, *other))
    if fst_type != dict:
        raise ValueError(
            f'Can merge only iterables or mappings not {(fst, snd, *other)}'
        )
    return {
        k: merge(*(map(itemgetter(1), values))) for k, values in
        groupby(
            chain.from_iterable(map(dict.items, (fst, snd, *other))),
            key=itemgetter(0)
        )
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
            (transformers[schema['type']](*values) for _, values in basecases),
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
    return dict(properties)


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
