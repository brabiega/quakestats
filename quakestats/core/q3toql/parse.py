"""

- Log stream
- log separator (mby md5sum now?)
- match log
- match log parser
- match events (middle form, CPMA, BASEq3, OSP -> middle form -> QL)
- to QL (events to QLMatch) - produces QLMatch


for QL
- QL separator - produces QLMatch


"""


def games(raw_data: str, mod_hint: str):
    """
    raw_data: raw string of quake log
    mod_name: name of game mod [baseq3, osp, cpma]
    """
    assert mod_hint in ['baseq3', 'osd', 'cpma']
    # TODO
    raise NotImplementedError()
