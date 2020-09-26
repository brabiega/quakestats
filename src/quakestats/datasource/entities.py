class Q3Match(dict):
    def __str__(self):
        return f"Q3Match({self.match_guid} - {self.start_date})"

    @property
    def match_guid(self):
        return self['match_guid']

    @property
    def start_date(self):
        return self['start_date']
