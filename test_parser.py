from parser import flat_namespace_to_dict

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
