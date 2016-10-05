import json
import pytest
from parser import flat_namespace_to_dict
from parser import schema_to_kwargs
from parser import common_kwargs
from parser import arguments


def test_parser():
    config = (('some.arg1', 1), ('some.arg2', 2), ('level0', 0))
    expected_result = {
        'some': {
            'arg1': 1,
            'arg2': 2,
        },
        'level0': 0,
    }
    assert expected_result == flat_namespace_to_dict(config)


def test_common_kwargs():
    schema = {'description': 'd'}
    expected_kwargs = {'required': True, 'name': 't', 'help': 'd'}
    assert expected_kwargs == common_kwargs(schema, name='t', required=True)


def test_schema_to_kwargs():
    schema = {
        'type': 'object', 'properties': {
            'p0': {
                'type': 'integer',
            },
            'p1': {
                'type': 'array',
                'items': [
                    {'type': 'integer'},
                ],
            }
        }
    }
    expected_kwargs = {
        arguments(type=json.loads, name='n', nargs=None),
        arguments(type=int, name='n.p0', nargs=None),
        arguments(type=int, name='n.p1', nargs='+'),
    }
    assert expected_kwargs == set(schema_to_kwargs(schema, name='n', required=False))
