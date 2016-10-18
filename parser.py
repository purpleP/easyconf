import json
from collections import Mapping
from argparse import ArgumentParser
from collections import namedtuple
from itertools import chain
from more_functools import merge
from jsonschema import validate
from split import groupby


def parse_args(schema):
    namespace = make_argparser(schema).parse_args()
    conf = namespace_to_dict(namespace)
    validate(conf, schema)
    return conf


def paths_from_namespace(namespace_dict):
    return (
        (k.split('.'), v)
        for k, v in namespace_dict.items() if v is not None
    )


def namespace_to_dict(namespace):
    namespace_dict = vars(namespace)
    defaults = namespace_dict.pop('conf', {})
    conf = dict_from_paths(*paths_from_namespace(namespace_dict))['conf']
    return merge(defaults, conf)


def dict_from_paths(*paths):
    def new_path(path):
        (key, *rest), value = path
        return rest, value
    if len(paths) == 1 and len(paths[0][0]) == 0:
        return paths[0][1]
    return {
        key: dict_from_paths(*map(new_path, remaining_paths))
        for key, remaining_paths in groupby(lambda ks: ks[0][0], paths)
    }


def chain_path(key, path):
    return chain((key,), path[0]), path[1]


def paths_from_dict(dct):
    def make_path(k, v):
        if isinstance(v, Mapping):
            map(partial(chain_path, k), paths_frm_dict(v))
        else:
            ((key,), v)
    return (make_path(k, v) for k, v in dct.items())


def make_argparser(schema):
    parser = ArgumentParser(description=schema.get('description', ''))
    for kwargs in schema_to_kwargs(schema, name='conf', required=False):
        name = kwargs.pop('name')
        parser.add_argument(name, **kwargs)
    return parser


def schema_to_kwargs(schema, name, required):
    kwargs = {**common_kwargs(schema, name, required), **specific_kwargs(schema)}
    flattened_dict_args = ()
    if schema['type'] == 'object':
        required = set(schema.get('required', ()))
        flattened_dict_args = chain.from_iterable(
            schema_to_kwargs(pschema, '.'.join((name, pname)), pname in required)
            for pname, pschema in schema['properties'].items()
        )
    return chain((kwargs,), flattened_dict_args)
    


def specific_kwargs(schema):
    kwargs = {}
    type = schema['type']
    if type == 'array':
        if len(schema['items']) > 1:
            raise Exception(
                'Easyconf doesn\'t support array with tuple validation.\n{}'.format(schema)
            )
        kwargs['type'] = jsonschema_types[schema['items'][0]['type']]
        kwargs['nargs'] = '+'
    elif type == 'object':
        kwargs['type'] = json.loads
    else:
        kwargs['type'] = jsonschema_types[type]
    return kwargs


def common_kwargs(schema, name, required):
    result = dict(
        name='--' + name,
        help=schema.get('description', ''),
    )
    if required:
        result['required'] = True
    return result

jsonschema_types = {
    'integer': int,
    'number': float,
    'boolean': bool,
    'string': str,
    'object': json.loads,
}
