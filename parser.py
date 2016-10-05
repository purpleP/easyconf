import json
from argparse import ArgumentParser
from collections import namedtuple
from itertools import chain
from split import groupby


Arguments = namedtuple('Arguments', 'type nargs name required help')


def arguments(type=None, nargs=None, name=None, help='', required=False):
    return Arguments(type, nargs, name, required, help)


def flat_namespace_to_dict(namespace):
    splitted = ((tuple(key.split('.')), value) for key, value in namespace)
    return make_dict(*splitted)


def make_dict(*paths):
    def new_path(path):
        (key, *rest), value = path
        return rest, value
    if len(paths) == 1 and len(paths[0][0]) == 0:
        return paths[0][1]
    return {
        key: make_dict(*map(new_path, remaining_paths))
        for key, remaining_paths in groupby(lambda ks: ks[0][0], paths)
    }


# def make_argparser(schema):
#     parser = ArgumentParser(description=schema.get('description', ''))
#     required = set(schema['required'])
#     (
#         for name, property in schema['properties'].items()
#     )

def schema_to_kwargs(schema, name, required):
    kwargs = {**common_kwargs(schema, name, required), **specific_kwargs(schema)}
    args = arguments(**kwargs)
    flattened_dict_args = ()
    if schema['type'] == 'object':
        required = set(schema.get('required', ()))
        flattened_dict_args = chain.from_iterable(
            schema_to_kwargs(pschema, '.'.join((name, pname)), pname in required)
            for pname, pschema in schema['properties'].items()
        )
    return chain((args,), flattened_dict_args)
    


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
    return dict(
        required=required,
        name=name,
        help=schema.get('description', ''),
    )

jsonschema_types = {
    'integer': int,
    'number': float,
    'boolean': bool,
    'string': str,
    'object': json.loads,
}
