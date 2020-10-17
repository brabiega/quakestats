from .osp import (
    OspParserMixin,
)


class EdawnParserMixin(OspParserMixin):
    """
    Edawn log format is super close to OSP
    """
    STAT_WEAPON_MAP = {
        'Machinegun': 'MACHINEGUN',
        'Shotgun': 'SHOTGUN',
        'G.Launcher': 'GRENADE',
        'R.Launcher': 'ROCKET',
        'Lightning': 'LIGHTNING',
        'Plasmagun': 'PLASMA',
        'Gauntlet': 'GAUNTLET',
        'Railgun': 'RAILGUN',
        'BFG': 'BFG',
    }
