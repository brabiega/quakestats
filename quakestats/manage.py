from passlib.hash import pbkdf2_sha256
from os import path, listdir
from quakestats import dataprovider
from quakestats.dataprovider import quake3, analyze

import logging


logger = logging.getLogger(__name__)


def set_admin_password(db, password):
    assert password
    assert len(password) > 3
    hashpass = pbkdf2_sha256.hash(password)
    result = db.user.update_one(
        {'username': 'admin'},
        {'$set': {'username': 'admin', 'password': hashpass}},
        upsert=True
    )
    return result


def rebuild_db(data_dir, server_domain, data_store):
    # TODO add tests

    data_store().prepare_for_rebuild()

    counter = 0
    for f in listdir(data_dir):
        with open(path.join(data_dir, f)) as fh:
            data = fh.read()
            match = {
                'EVENTS': data.splitlines()
            }

            source_type = 'Q3'
            transformer = quake3.Q3toQL(match['EVENTS'])
            transformer.server_domain = server_domain

            try:
                transformer.process()

            except Exception as e:
                # TODO save for investigation if error
                logger.exception(e)
                continue

            results = transformer.result

            # PREPROCESS
            preprocessor = dataprovider.MatchPreprocessor()
            preprocessor.process_events(results['events'])

            if not preprocessor.finished:
                continue

            fmi = dataprovider.FullMatchInfo(
                events=preprocessor.events,
                match_guid=preprocessor.match_guid,
                duration=preprocessor.duration,
                start_date=results['start_date'],
                finish_date=results['finish_date'],
                server_domain=server_domain,
                source=source_type)

            analyzer = analyze.Analyzer()
            report = analyzer.analyze(fmi)
            try:
                data_store().store_analysis_report(report)
            except Exception:
                logger.error(
                    "Failed to process match with guid %s", fmi.match_guid
                )
                raise

            counter += 1

    data_store().post_rebuild()
    return counter
