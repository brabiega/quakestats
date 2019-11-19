from collections import defaultdict
from quakestats.web import app, data_store
from quakestats import dataprovider, manage
from quakestats.dataprovider import quake3, analyze
from os import path
import flask
import logging


logger = logging.getLogger('quakestats.webapp')


class QJsonEncoder(flask.json.JSONEncoder):
    def default(self, o):  # noqa
        # TODO too tightly coupled with internal data structures
        if isinstance(o, quake3.PlayerId):
            return str(o.steam_id)
        return flask.json.JSONEncoder.default(self, o)


def auth(token):
    return token == app.config['ADMIN_TOKEN']


@app.route('/api/v2/match')
def api2_matches():
    return flask.jsonify(data_store().get_matches(132))


@app.route('/api/v2/match/<match_guid>/metadata')
def api2_match_metadata(match_guid):
    return flask.jsonify(data_store().get_match_metadata(match_guid))


@app.route('/api/v2/match/<match_guid>/players')
def api2_match_players(match_guid):
    return flask.jsonify(data_store().get_match_players(match_guid))


@app.route('/api/v2/match/<match_guid>/teams')
def api2_match_team_lifecycle(match_guid):
    return flask.jsonify(data_store().get_team_lifecycle(match_guid))


@app.route('/api/v2/player/<player_id>')
def api2_player(player_id):
    return flask.jsonify(data_store().get_player(player_id))


@app.route('/api/v2/match/<match_guid>/score')
def api2_match_scores(match_guid):
    return flask.jsonify(data_store().get_match_scores(match_guid))


@app.route('/api/v2/match/<match_guid>/special')
def api2_match_special(match_guid):
    return flask.jsonify(data_store().get_match_special_scores(match_guid))


@app.route('/api/v2/match/<match_guid>/kill')
def api2_match_kill(match_guid):
    return flask.jsonify(data_store().get_match_kills(match_guid))


@app.route('/api/v2/match/<match_guid>/badge')
def api2_match_badge(match_guid):
    return flask.jsonify(data_store().get_match_badges(match_guid))


@app.route('/api/v2/match/<match_guid>/player_stats')
def api2_match_player_stats(match_guid):
    return flask.jsonify(data_store().get_match_player_stats(match_guid))


@app.route('/api/v2/board/badges')
def api2_board_badges():
    latest = flask.request.args.get('latest', default=None)
    latest = int(latest) if latest else None
    return flask.jsonify(data_store().get_badge_sum(latest))


@app.route('/api/v2/board/total')
def api2_board_total():
    latest = flask.request.args.get('latest', default=None)
    latest = int(latest) if latest else None
    return flask.jsonify(data_store().get_total_stats(latest))


@app.route('/api/v2/players')
def api2_board_players():
    return flask.jsonify(data_store().get_players())


@app.route('/api/v2/maps')
def api2_maps():
    return flask.jsonify(data_store().get_map_stats())


@app.route('/api/v2/player/<player_id>/kills')
def api2_player_kills(player_id):
    return flask.jsonify(data_store().get_player_kills(player_id))


@app.route('/api/v2/player/<player_id>/deaths')
def api2_player_deaths(player_id):
    return flask.jsonify(data_store().get_player_deaths(player_id))


@app.route('/api/v2/player/<player_id>/badges')
def api2_player_badges(player_id):
    return flask.jsonify(data_store().get_player_badges(player_id))


@app.route('/api/v2/map/size', methods=['POST'])
def api2_map_info():
    if flask.g.user == 'admin':
        data_store().set_map_info(
            flask.request.json['map_name'],
            flask.request.json.get('size', None),
            flask.request.json.get('rate', None),
        )
        return 'OK'
    return 'Bye'


@app.route('/api/v2/upload', methods=['POST'])
def api2_upload():
    if not auth(flask.request.form['token']):
        return 'Bye'

    # TODO this code should be rewritten
    if 'file' not in flask.request.files:
        raise Exception("No Files")

    req_file = flask.request.files['file']
    data = req_file.read().decode("utf-8")
    server_domain = app.config['SERVER_DOMAIN']
    source_type = 'Q3'
    feeder = quake3.Q3MatchFeeder()
    matches = []

    for line in data.splitlines():
        try:
            feeder.feed(line)
        except quake3.FeedFull:
            matches.append(feeder.consume())
            feeder.feed(line)

    final_results = []
    errors = 0
    for match in matches:
        # TRANSFORM TO QL
        transformer = quake3.Q3toQL(match['EVENTS'])
        transformer.server_domain = server_domain

        try:
            transformer.process()

        except Exception as e:
            # TODO save for investigation if error
            errors += 1
            logger.exception(e)
            continue

        results = transformer.result

        # PREPROCESS
        preprocessor = dataprovider.MatchPreprocessor()
        preprocessor.process_events(results['events'])

        if not preprocessor.finished:
            continue

        if app.config['RAW_DATA_DIR']:
            base = app.config['RAW_DATA_DIR']
            preprocessor.match_guid
            p = path.join(base, "{}.log".format(preprocessor.match_guid))
            with open(p, 'w') as fh:
                for line in match['EVENTS']:
                    fh.write(line)
                    fh.write('\n')

        final_results.append(dataprovider.FullMatchInfo(
            events=preprocessor.events,
            match_guid=preprocessor.match_guid,
            duration=preprocessor.duration,
            start_date=results['start_date'],
            finish_date=results['finish_date'],
            server_domain=server_domain,
            source=source_type))

        fmi = final_results[-1]
        analyzer = analyze.Analyzer()
        report = analyzer.analyze(fmi)
        data_store().store_analysis_report(report)

    return flask.jsonify({
        "ACCEPTED_MATCHES": [
            r.get_summary() for r in final_results],
        "ERRORS": errors
    })


@app.route('/api/v2/admin/match/import', methods=['POST'])
def api2_admin_match_import():
    """
    Import q3 match log previously stored in RAW_DATA_DIR
    The log file should contain single match events, excluding
    match delimiter (-----)
    """
    if not auth(flask.request.form['token']):
        return 'Bye'

    # TODO this code should be rewritten
    if 'file' not in flask.request.files:
        raise Exception("No Files")

    req_file = flask.request.files['file']
    data = req_file.read().decode("utf-8")
    match = {
        'EVENTS': data.splitlines()
    }

    server_domain = app.config['SERVER_DOMAIN']
    source_type = 'Q3'
    transformer = quake3.Q3toQL(match['EVENTS'])
    transformer.server_domain = server_domain

    try:
        transformer.process()

    except Exception as e:
        # TODO save for investigation if error
        logger.exception(e)
        return 'Failed'

    results = transformer.result

    # PREPROCESS
    preprocessor = dataprovider.MatchPreprocessor()
    preprocessor.process_events(results['events'])

    if not preprocessor.finished:
        return 'Match not finished'

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
    data_store().store_analysis_report(report)
    return 'OK'


@app.route('/api/v2/admin/players/merge', methods=['POST'])
def api2_admin_players_merge():
    # TODO PROPER AUTH
    if not auth(flask.request.form['token']):
        return 'Bye'

    source_id = flask.request.form['source_player_id']
    target_id = flask.request.form['target_player_id']
    data_store().merge_players(source_id, target_id)
    return 'OK'


@app.route('/api/v2/admin/rebuild', methods=['POST'])
def api2_admin_rebuild():
    if not auth(flask.request.form['token']):
        return 'Bye'

    match_count = manage.rebuild_db(
        app.config['RAW_DATA_DIR'],
        app.config['SERVER_DOMAIN'],
        data_store
    )

    return 'Processed {} matches\n'.format(match_count)


@app.route('/api/v2/admin/delete', methods=['POST'])
def api2_admin_delete():
    if not auth(flask.request.form['token']):
        return 'Bye'

    if not flask.request.form['match_guid']:
        return 'Bye'

    data_store().drop_match_info(
        flask.request.form['match_guid'])
    return 'OK'


@app.route('/api/v2/presence/<count>')
def api2_presence(count):
    try:
        count = int(count)
    except ValueError:
        flask.abort(400)

    ds = data_store()
    last_matches = ds.get_matches(count)

    player_ids_per_match = ds.get_match_participants(
        [m['match_guid'] for m in last_matches]
    )

    presence = defaultdict(lambda: 0)
    for match_players in player_ids_per_match.values():
        for player_id in match_players:
            presence[player_id] += 1

    players = ds.get_players(ids=[player_id for player_id in presence.keys()])
    return flask.jsonify({
        'presence': presence,
        'players': players,
    })