import json

import pytest

from easyconf import Buffered, group_by_argname


def test_buffered():
    b = Buffered(iter(range(2)))
    assert 0 == next(b)
    b.from_buffer = True
    assert 0 == next(b)
    assert 1 == next(b)
    b.from_buffer = True
    assert 1 == next(b)



def test_path_key_pairs():
    args = ('--conf.a', 'some', 'other', '--conf.b', 'foo')
    expected = [('a', ['some', 'other']), ('b', ['foo'])]
    assert expected == [(argname, list(values)) for argname, values in group_by_argname(args)]
