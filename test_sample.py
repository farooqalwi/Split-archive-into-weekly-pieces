"""
You can auto-discover and run all tests with this command:

    py.test

Documentation: https://docs.pytest.org/en/latest/
"""


def inc(num):
    """This function is for increasing 1 in any number"""
    return num + 1


def test_answer():
    """This function is for answer testing"""
    assert inc(3) == 4
