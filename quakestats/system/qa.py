"""
Quality Assurance stuff
Not sure where to put it
"""


def _regen_asserts(data, accessor: str = 'e'):
    if isinstance(data, int):
        print(f'assert {accessor} == {data}  # noqa')
    elif isinstance(data, str):
        print(f"assert {accessor} == '{data}'  # noqa")
    elif isinstance(data, bool):
        print(f"assert {accessor} is {data}  # noqa")
    elif data is None:
        print(f"assert {accessor} is None  # noqa")
    elif isinstance(data, dict):
        # go deeper
        for k, v in data.items():
            nested_accessor = f"{accessor}['{k}']"
            _regen_asserts(v, nested_accessor)
    # namedtuple
    elif isinstance(data, tuple) and getattr(data, "_fields", None):
        fields = data._fields
        for field in fields:
            nested_accessor = f"{accessor}.{field}"
            _regen_asserts(getattr(data, field), nested_accessor)
    elif isinstance(data, (list, tuple)):
        for idx, v in enumerate(data):
            nested_accessor = f"{accessor}[{idx}]"
            _regen_asserts(v, nested_accessor)
    else:
        raise NotImplementedError(f"{data} of {type(data)}")
