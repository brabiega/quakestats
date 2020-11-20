import os

import quakestats
from quakestats.system.conf import (
    ENV_VAR_NAME,
    get_conf_val,
)
from quakestats.system.context import (
    SystemContext,
)


class HealthInfo:
    OK = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    CRITICAL = 4

    def __init__(self, ctx: SystemContext):
        self.ctx = ctx
        self.status = {}

    def add_status(self, key, level, comment):
        assert key not in self.status
        self.status[key] = (level, comment)

    def check_version(self):
        return self.INFO, quakestats.VERSION

    def check_quakestats_var(self):
        settings_file = os.environ.get(ENV_VAR_NAME)
        if settings_file is None:
            return self.ERROR, "{QUAKESTATS_SETTINGS} env var not set"

        else:
            return self.OK, settings_file

    def check_settings_data_dir(self):
        data_dir = get_conf_val("RAW_DATA_DIR")
        if data_dir:
            return self.OK, data_dir
        else:
            return self.WARN, "Data dir is not configured"

    def check_webapp_loadable(self):
        from quakestats.web import app  # noqa

        return self.OK, "Quakestats webapp is loadable"

    def check_db_access(self):
        result = self.ctx.ds.db.command("ping")
        if result["ok"]:
            return self.OK, str(result)
        else:
            return self.ERROR, str(result)

    def run(self):
        for key, check in {
            "app -> version": self.check_version,
            "settings -> env var": self.check_quakestats_var,
            "settings -> RAW_DATA_DIR": self.check_settings_data_dir,
            "db -> ping": self.check_db_access,
            "webapp -> loadable": self.check_webapp_loadable,
        }.items():
            try:
                level, comment = check()
                self.add_status(key, level, comment)

            except Exception as e:
                self.add_status(key, self.ERROR, str(e))

        return self.status
