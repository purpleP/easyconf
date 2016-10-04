from argparse import ArgumentParser
from split import groupby


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


def make_argparser(schema):
    parser = ArgumentParser(description=schema.get('description', ''))
    required = set(schema['required'])
    (
        
        for name, property in schema['properties'].items()
    )

property_to_argument = {
    'integer': int,
    'number': float,
    'boolean': bool,
}


def to_argument(property, required):
    type = property['type']
    if type != 'object'
        keywords = {'name': property['name']}
        if required:
            keywords['required'] = True
        keywords['type'] = jsonschema_type_to_python[type]
    return {}


class Properties:
    @staticmethod
    def integer(property):
        {'type': int}
