"""
    For now mostly FFA is supported
    Events implementation:
        [x] MATCH_STARTED
        [x] MATCH_REPORT - partial
        [x] PLAYER_CONNECT
        [x] PLAYER_DISCONNECT
        [ ] PLAYER_STATS - partially possible, can live without it now
        [x] PLAYER_KILL - partial
        [x] PLAYER_DEATH - partial
        [x] PLAYER_SWITCHTEAM
        [ ] PLAYER_MEDAL - need to trace game :/
        [ ] ROUND_OVER - TODO - e.g for CTF/TDM/CA

    Supported MODS:
        [x] OSP
        [ ] vanilla q3 - doesn't send ServerTime

    TODO:
        - consider building match id from hash of whole match log
          would be more reliable and would work without ServerTime message
        - how to set game start/finish dates in vq3
"""

# TODO following import is not needed here, it is only referenced by other
# modules and tests while it shouldn't be
from quakestats.dataprovider.quake3.feeder import Q3MatchFeeder, FeedFull
from quakestats.dataprovider.quake3.transformer import Q3toQL, PlayerId


__all__ = ['*']
