import logging
from collections import (
    defaultdict,
)
from os import (
    path,
)

import flask

from quakestats import (
    dataprovider,
    manage,
)
from quakestats.dataprovider import (
    analyze,
    quake3,
)
from quakestats.web.app import (
    app,
    data_store,
)

logger = logging.getLogger("quakestats.webapp")


def auth(token):
    return token == app.config["ADMIN_TOKEN"]


@app.route("/api/v2/matches")
def api2_matches():
    return flask.jsonify(data_store().get_matches(25))


@app.route("/api/v2/matches/all")
def api2_matches_all():
    return flask.jsonify(data_store().get_matches())


@app.route("/api/v2/match/<match_guid>/metadata")
def api2_match_metadata(match_guid):
    return flask.jsonify(data_store().get_match_metadata(match_guid))


@app.route("/api/v2/match/<match_guid>/players")
def api2_match_players(match_guid):
    return flask.jsonify(data_store().get_match_players(match_guid))


@app.route("/api/v2/match/<match_guid>/teams")
def api2_match_team_lifecycle(match_guid):
    return flask.jsonify(data_store().get_team_lifecycle(match_guid))


@app.route("/api/v2/player/<player_id>")
def api2_player(player_id):
    return flask.jsonify(data_store().get_player(player_id))


@app.route("/api/v2/match/<match_guid>/score")
def api2_match_scores(match_guid):
    return flask.jsonify(data_store().get_match_scores(match_guid))


@app.route("/api/v2/match/<match_guid>/special")
def api2_match_special(match_guid):
    return flask.jsonify(data_store().get_match_special_scores(match_guid))


@app.route("/api/v2/match/<match_guid>/kill")
def api2_match_kill(match_guid):
    return flask.jsonify(data_store().get_match_kills(match_guid))


@app.route("/api/v2/match/<match_guid>/badge")
def api2_match_badge(match_guid):
    return flask.jsonify(data_store().get_match_badges(match_guid))


@app.route("/api/v2/match/<match_guid>/player_stats")
def api2_match_player_stats(match_guid):
    return flask.jsonify(data_store().get_match_player_stats(match_guid))


@app.route("/api/v2/board/badges")
def api2_board_badges():
    latest = flask.request.args.get("latest", default=None)
    latest = int(latest) if latest else None
    return flask.jsonify(data_store().get_badge_sum(latest))


@app.route("/api/v2/board/total")
def api2_board_total():
    latest = flask.request.args.get("latest", default=None)
    latest = int(latest) if latest else None
    return flask.jsonify(data_store().get_total_stats(latest))


@app.route("/api/v2/players")
def api2_board_players():
    return flask.jsonify(data_store().get_players())


@app.route("/api/v2/maps")
def api2_maps():
    return flask.jsonify(data_store().get_map_stats())


@app.route("/api/v2/player/<player_id>/kills")
def api2_player_kills(player_id):
    return flask.jsonify(data_store().get_player_kills(player_id))


@app.route("/api/v2/player/<player_id>/deaths")
def api2_player_deaths(player_id):
    return flask.jsonify(data_store().get_player_deaths(player_id))


@app.route("/api/v2/player/<player_id>/badges")
def api2_player_badges(player_id):
    return flask.jsonify(data_store().get_player_badges(player_id))


@app.route("/api/v2/map/size", methods=["POST"])
def api2_map_info():
    if flask.g.user == "admin":
        data_store().set_map_info(
            flask.request.json["map_name"],
            flask.request.json.get("size", None),
            flask.request.json.get("rate", None),
        )
        return "OK"
    return "Bye"


def _process_match(match):
    server_domain = app.config["SERVER_DOMAIN"]
    source_type = "Q3"

    # TRANSFORM TO QL
    transformer = quake3.Q3toQL(match["EVENTS"])
    transformer.server_domain = server_domain

    transformer.process()
    results = transformer.result

    # PREPROCESS
    preprocessor = dataprovider.MatchPreprocessor()
    preprocessor.process_events(results["events"])

    if not preprocessor.finished:
        return None

    if app.config["RAW_DATA_DIR"]:
        base = app.config["RAW_DATA_DIR"]
        preprocessor.match_guid
        p = path.join(base, "{}.log".format(preprocessor.match_guid))
        with open(p, "w") as fh:
            for line in match["EVENTS"]:
                fh.write(line)
                fh.write("\n")

    fmi = dataprovider.FullMatchInfo(
        events=preprocessor.events,
        match_guid=preprocessor.match_guid,
        duration=preprocessor.duration,
        start_date=results["start_date"],
        finish_date=results["finish_date"],
        server_domain=server_domain,
        source=source_type,
    )

    analyzer = analyze.Analyzer()
    report = analyzer.analyze(fmi)
    data_store().store_analysis_report(report)
    return fmi


@app.route("/api/v2/upload/json", methods=["POST"])
def api2_upload_json():
    data = flask.request.json

    if not data:
        flask.abort(400)

    if not auth(data.get("TOKEN", None)):
        flask.abort(400)

    fmi = _process_match(data)

    if not fmi:
        return "Nothing to process"
    else:
        return flask.jsonify(fmi.get_summary())


@app.route("/api/v2/upload", methods=["POST"])
def api2_upload():
    if not auth(flask.request.form["token"]):
        return "Bye"

    # TODO this code should be rewritten
    if "file" not in flask.request.files:
        raise Exception("No Files")

    req_file = flask.request.files["file"]
    data = req_file.read().decode("utf-8")

    feeder = quake3.Q3MatchFeeder()
    matches = []

    for line in data.splitlines():
        try:
            feeder.feed(line)
        except quake3.FeedFull:
            matches.append(feeder.consume())
            feeder.feed(line)

    errors = 0
    final_results = []
    for match in matches:
        try:
            fmi = _process_match(match)
            if fmi:
                final_results.append(fmi)

        except Exception as e:
            # TODO save for investigation
            logger.exception(e)
            errors += 1

    return flask.jsonify(
        {
            "ACCEPTED_MATCHES": [r.get_summary() for r in final_results],
            "ERRORS": errors,
        }
    )


@app.route("/api/v2/admin/match/import", methods=["POST"])
def api2_admin_match_import():
    """
    Import q3 match log previously stored in RAW_DATA_DIR
    The log file should contain single match events, excluding
    match delimiter (-----)
    """
    if not auth(flask.request.form["token"]):
        return "Bye"

    # TODO this code should be rewritten
    if "file" not in flask.request.files:
        raise Exception("No Files")

    req_file = flask.request.files["file"]
    data = req_file.read().decode("utf-8")
    match = {"EVENTS": data.splitlines()}

    server_domain = app.config["SERVER_DOMAIN"]
    source_type = "Q3"
    transformer = quake3.Q3toQL(match["EVENTS"])
    transformer.server_domain = server_domain

    try:
        transformer.process()

    except Exception as e:
        # TODO save for investigation if error
        logger.exception(e)
        return "Failed"

    results = transformer.result

    # PREPROCESS
    preprocessor = dataprovider.MatchPreprocessor()
    preprocessor.process_events(results["events"])

    if not preprocessor.finished:
        return "Match not finished"

    fmi = dataprovider.FullMatchInfo(
        events=preprocessor.events,
        match_guid=preprocessor.match_guid,
        duration=preprocessor.duration,
        start_date=results["start_date"],
        finish_date=results["finish_date"],
        server_domain=server_domain,
        source=source_type,
    )

    analyzer = analyze.Analyzer()
    report = analyzer.analyze(fmi)
    data_store().store_analysis_report(report)
    return "OK"


@app.route("/api/v2/admin/players/merge", methods=["POST"])
def api2_admin_players_merge():
    # TODO PROPER AUTH
    if not auth(flask.request.form["token"]):
        return "Bye"

    source_id = flask.request.form["source_player_id"]
    target_id = flask.request.form["target_player_id"]
    data_store().merge_players(source_id, target_id)
    return "OK"


@app.route("/api/v2/admin/rebuild", methods=["POST"])
def api2_admin_rebuild():
    if not auth(flask.request.form["token"]):
        return "Bye"

    match_count = manage.rebuild_db(
        app.config["RAW_DATA_DIR"], app.config["SERVER_DOMAIN"], data_store
    )

    return "Processed {} matches\n".format(match_count)


@app.route("/api/v2/admin/delete", methods=["POST"])
def api2_admin_delete():
    if not auth(flask.request.form["token"]):
        return "Bye"

    if not flask.request.form["match_guid"]:
        return "Bye"

    data_store().drop_match_info(flask.request.form["match_guid"])
    return "OK"


@app.route("/api/v2/presence/<count>")
def api2_presence(count):
    try:
        count = int(count)
    except ValueError:
        flask.abort(400)

    ds = data_store()
    last_matches = ds.get_matches(count)

    player_ids_per_match = ds.get_match_participants(
        [m["match_guid"] for m in last_matches]
    )

    presence = defaultdict(lambda: 0)
    for match_players in player_ids_per_match.values():
        for player_id in match_players:
            presence[player_id] += 1

    players = ds.get_players(ids=[player_id for player_id in presence.keys()])
    return flask.jsonify({"presence": presence, "players": players})


@app.route("/api/v2/total_stats", methods=['POST'])
def api2_total_stats():
    """
    A little bit hacked endpoint to fetch total stats
    """
    # auth required to prevent DOS as this call is quite expensive
    if not auth(flask.request.form["token"]):
        return "Bye"

    ds = data_store()
    db = ds.db
    matches = list(db.match.find(
        {}, {"_id": 0}
    ))
    result = {}
    result['total_matches'] = len(matches)
    result['total_time_h'] = sum(m['duration'] for m in matches) / (60*60)
    result['total_time_d'] = result['total_time_h'] / 24

    all_players = {
        e['id']: e for e in db.player.find({}, {'_id': 0})
    }

    kills = list(db.kill.find(
        {}, {'_id': 0}
    ))
    non_selfkills = [
        k for k in kills
        if k['killer_id'] != 'q3-world' and k['killer_id'] != k['victim_id']
    ]
    player_stats = list(db.player_stats.find())

    result['total_matches'] = len(matches)
    result['total_time_h'] = sum(m['duration'] for m in matches) / (60*60)
    result['total_time_d'] = result['total_time_h'] / 24
    result['total_kills'] = len(non_selfkills)
    result['total_self_kills'] = len([
        k for k in kills
        if k['killer_id'] == 'q3-world' or k['killer_id'] == k['victim_id']
    ])
    result['world_only_kills'] = len([
        k for k in kills
        if k['killer_id'] == 'q3-world'
    ])
    result['total_players'] = len(all_players)
    result['total_player_mandays'] = (len(player_stats) * 15) / (60 * 8)
    result['total_damage_dealt'] = 0
    result['total_damage_received'] = 0

    player_matches = {}
    for player_stat in player_stats:
        pid = player_stat['player_id']
        if pid not in player_matches:
            player_matches[pid] = {
                'total_games': 0,
                'player_id': pid,
                'total_damage_dealt': 0,
                'total_damage_received': 0,
                'player_name': None
            }
        info = player_matches[pid]
        info['total_games'] += 1
        info['total_damage_dealt'] += player_stat['damage_dealt']
        info['total_damage_received'] += player_stat['damage_taken']
        info['player_name'] = all_players[pid]['name']

        result['total_damage_dealt'] += player_stat['damage_dealt']
        result['total_damage_received'] += player_stat['damage_taken']

    result['top10_played_matches'] = sorted([
        (p['total_games'], p['player_name'])
        for p in player_matches.values()
    ])[-10:]
    result['top10_played_damage_dealt'] = sorted([
        (p['total_damage_dealt'], p['player_name'])
        for p in player_matches.values()
    ])[-10:]
    result['top10_played_damage_received'] = sorted([
        (p['total_damage_received'], p['player_name'])
        for p in player_matches.values()
    ])[-10:]

    player_kd = {}
    for kill in kills:
        kpid = kill['killer_id']
        vpid = kill['victim_id']

        kstat = player_kd.setdefault(
            kpid, {
                'selfkills': 0, 'kills': 0, 'deaths': 0,
                'name': all_players[kpid]['name']
            }
        )
        vstat = player_kd.setdefault(
            vpid, {
                'selfkills': 0, 'kills': 0, 'deaths': 0,
                'name': all_players[vpid]['name']
            }
        )
        kstat['kills'] += 1
        vstat['deaths'] += 1

        if kpid == vpid or kpid == 'q3-world':
            vstat['selfkills'] += 1

    result['top10_kills'] = sorted([
        (k['kills'], k['name']) for k in player_kd.values()
    ])[-10:]
    result['top10_deaths'] = sorted([
        (k['deaths'], k['name']) for k in player_kd.values()
    ])[-10:]

    result['top10_selfkills'] = sorted([
        (k['selfkills'], k['name']) for k in player_kd.values()
    ])[-10:]

    result['unique_players_2+matches'] = len(
        [e for e in player_matches.values() if e['total_games'] > 2]
    )
    result['regular_players_15+matches'] = len(
        [e for e in player_matches.values() if e['total_games'] > 15]
    )
    return flask.jsonify({"matches": result})
