class Event(dict):
    """
    Helper class wrapping raw QL events.
    Provides shortcuts to access interesting fields.
    Improves code readability and keeps dict inspection in single place
    """
    @classmethod
    def from_dict(cls, data):
        classes = {
            'PLAYER_KILL': EventPlayerKill
        }
        try:
            cls = classes[data['TYPE']]
        except KeyError:
            pass
        obj = cls(data)
        return obj

    # common properties, should be available in all events
    @property
    def type(self):
        return self['TYPE']

    @property
    def data(self):
        return self['DATA']

    @property
    def time(self):
        return self.data['TIME']


class EventPlayerKill(Event):
    @property
    def victim_id(self):
        return self.data['VICTIM']['STEAM_ID']

    @property
    def victim_name(self):
        return self.data['VICTIM']['NAME']

    @property
    def killer_id(self):
        return self.data['KILLER']['STEAM_ID']

    @property
    def killer_name(self):
        return self.data['KILLER']['NAME']

    @property
    def mod(self):
        return self.data['MOD']
