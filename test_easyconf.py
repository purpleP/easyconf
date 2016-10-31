import json
import pytest
from easyconf import dict_from_paths
from easyconf import schema_to_kwargs
from easyconf import common_kwargs
from frozendict import frozendict


def test_make_dict():
    paths = (
        (('some', 'arg1'), 1),
        (('some', 'arg2'), 2),
        (('level0',), 0),
    )
    expected_result = {
        'some': {
            'arg1': 1,
            'arg2': 2,
        },
        'level0': 0,
    }
    assert expected_result == dict_from_paths(*paths)


def test_common_kwargs():
    schema = {'description': 'd'}
    expected_kwargs = {'name': '--t', 'help': 'd'}
    assert expected_kwargs == common_kwargs(schema, name='t')


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
        frozendict(type=json.loads, help='', name='--n'),
        frozendict(type=int, help='', name='--n.p0'),
        frozendict(type=int, help='', name='--n.p1', nargs='+'),
    }
    assert expected_kwargs == set(
        map(frozendict, schema_to_kwargs(schema, name='n'))
    )
