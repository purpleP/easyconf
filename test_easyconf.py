import json

import pytest

from easyconf import Buffered, make_value, make_paths, merge


def test_buffered():
    b = Buffered(iter(range(2)))
    assert 0 == next(b)
    b.from_buffer = True
    assert 0 == next(b)
    assert 1 == next(b)
    with pytest.raises(StopIteration):
        next(b)


@pytest.mark.parametrize(
    'a,b,expected',
    (
        ([1], [2], [1, 2]),
        ({'a': 1}, {'b': 2}, {'a': 1, 'b': 2}),
    )
)
def test_merge(a, b, expected):
    assert expected == merge(a, b)


@pytest.mark.parametrize(
    'a,b,exc',
    (
        (1, 2, ValueError),
        ({'a': 1}, {'a': 2}, ValueError),
    )
)
def test_merge_exceptions(a, b, exc):
    with pytest.raises(exc):
        merge(a, b)


def test_make_value():
    conf_schema = {
        'type': 'object',
        'properties': {
            'a': {'type': 'array', 'items': {'type': 'integer'}},
            'b': {
                'type': 'object',
                'properties': {
                    'c': {'type': 'array', 'items': {'type': 'integer'}},
                    'd': {'type': 'array', 'items': {'type': 'integer'}},
                },
            },
            'c': {'type': 'integer'},
            'd': {
                'type': 'array',
                'items': {'type': 'object', 'properties': {'a': {'type': 'integer'}}}
            },
            'e': {
                'type': 'object',
                'additionalProperties': {'type': 'integer'},
            },
            'f': {'type': 'boolean'},
        },
    }
    schema = {'type': 'object', 'properties': {'conf': conf_schema}}
    args = (
        'some', '--not', 'confarg',
        '--conf.a', '1', '2',
        '--conf.b', json.dumps({'c': [2], 'd': [3]}),
        '--conf.b.c', '3',
        '--conf.b.d', '4',
        '--conf.c', '4',
        '--conf.d', json.dumps([{'a': 1}]),
        '--conf.e', json.dumps({'a': 1}),
        '--conf.f',
    )
    expected = dict(a=[1, 2], b=dict(c=[2, 3], d=[3, 4]), c=4, d=[{'a': 1}], e={'a': 1}, f=True)
    paths = tuple(make_paths(args))
    assert {'conf': expected} == make_value(schema, paths)
