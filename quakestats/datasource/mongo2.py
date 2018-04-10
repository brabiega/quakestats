"""
TODO add documentation
"""
import pymongo


class DataStoreMongo():
    def __init__(self, db):
        self.db = db

    def store_analysis_report(self, analysis_report):
        match_guid = analysis_report.match_metadata.match_guid
        match_in_db = self.db.match.find_one({'match_guid': match_guid})
        if match_in_db:
            return False, match_guid

        self.store_match(analysis_report)
        self.store_players(analysis_report)
        self.store_team_lifecycle(analysis_report)
        self.store_scores(analysis_report)
        self.store_kills(analysis_report)
        self.store_special_scores(analysis_report)
        self.store_badges(analysis_report)
        return True, match_guid

    def merge_players(self, src_player_id, target_player_id):
        # TODO this can probably be tested properly only with integration tests
        self.db.badge.bulk_write([
            pymongo.UpdateMany(
                {'player_id': src_player_id},
                {'$set': {'player_id': target_player_id}})
        ])
        self.db.special_score.bulk_write([
            pymongo.UpdateMany(
                {'killer_id': src_player_id},
                {'$set': {'killer_id': target_player_id}}),
            pymongo.UpdateMany(
                {'victim_id': src_player_id},
                {'$set': {'victim_id': target_player_id}})
        ])
        self.db.kill.bulk_write([
            pymongo.UpdateMany(
                {'killer_id': src_player_id},
                {'$set': {'killer_id': target_player_id}}),
            pymongo.UpdateMany(
                {'victim_id': src_player_id},
                {'$set': {'victim_id': target_player_id}})
        ])
        self.db.score.bulk_write([
            pymongo.UpdateMany(
                {'player_id': src_player_id},
                {'$set': {'player_id': target_player_id}})
        ])
        self.db.team_switch.bulk_write([
            pymongo.UpdateMany(
                {'player_id': src_player_id},
                {'$set': {'player_id': target_player_id}})
        ])

    def store_match(self, analysis_report):
        match_info = self.attr2dict(
            analysis_report.match_metadata, [
                 'capture_limit',
                 'duration',
                 'exit_message',
                 'finish_date',
                 'frag_limit',
                 'game_type',
                 'map_name',
                 'match_guid',
                 'score_limit',
                 'server_domain',
                 'server_name',
                 'start_date',
                 'time_limit'])

        self.db.match.insert_one(match_info)

    def store_players(self, analysis_report):
        server_domain = analysis_report.match_metadata.server_domain

        operations = []
        for player_id, player_info in analysis_report.players.items():
            operations.append(pymongo.UpdateOne(
                {'id': player_id, 'server_domain': server_domain},
                {'$set': {
                    'server_domain': server_domain,
                    'name': player_info.name,
                    'id': player_id,
                    'model': player_info.model}},
                upsert=True))
        self.db.player.bulk_write(operations)

    def store_team_lifecycle(self, analysis_report):
        match_guid = analysis_report.match_metadata.match_guid
        result = []
        for switch in analysis_report.team_switches:
            result.append({
                'match_guid': match_guid,
                'game_time': switch[0],
                'player_id': switch[1],
                'from': switch[2],
                'to': switch[3],
            })
        self.db.team_switch.insert_many(result)

    def store_scores(self, analysis_report):
        match_guid = analysis_report.match_metadata.match_guid
        results = []
        for score in analysis_report.scores:
            results.append({
                'match_guid': match_guid,
                'game_time': score[0],
                'player_id': score[1],
                'score': score[2],
                'by': score[3]
            })
        self.db.score.insert_many(results)

    def store_kills(self, analysis_report):
        match_guid = analysis_report.match_metadata.match_guid
        results = []
        for kill in analysis_report.kills:
            results.append({
                'match_guid': match_guid,
                'game_time': kill[0],
                'killer_id': kill[1],
                'victim_id': kill[2],
                'by': kill[3]
            })
        self.db.kill.insert_many(results)

    def store_special_scores(self, analysis_report):
        match_guid = analysis_report.match_metadata.match_guid
        results = []
        for score_type, scores in analysis_report.special_scores.items():
            for score in scores:
                results.append({
                    'game_time': score[0],
                    'match_guid': match_guid,
                    'killer_id': score[1],  # TODO rename killer_id to scorer_id
                    'victim_id': score[2],  # TODO rename to scored_on
                    'score_type': score_type,
                    'value': score[3]})
        self.db.special_score.insert_many(results)

    def store_badges(self, analysis_report):
        match_guid = analysis_report.match_metadata.match_guid
        results = []
        for badge in analysis_report.badges:
            results.append({
                'match_guid': match_guid,
                'name': badge[0],
                'player_id': badge[1],
                'count': badge[2],
            })
        self.db.badge.insert_many(results)

    def attr2dict(self, obj, attributes):
        result = {}
        for attr in attributes:
            result[attr] = getattr(obj, attr)
        return result

    def strip_id(self, dict_or_list):
        if isinstance(dict_or_list, dict):
            del dict_or_list['_id']
            result = dict_or_list
        else:
            result = []
            for entry in dict_or_list:
                del entry['_id']
                result.append(entry)
        return result

    def get_matches(self, latest=None):
        if latest:
            result = self.db.match.find().sort('start_date', pymongo.DESCENDING).limit(latest)
        else:
            result = self.db.match.find()
        return self.strip_id(result)

    def get_match_players(self, match_guid):
        switches = self.db.team_switch.find({'match_guid': match_guid})
        player_ids = {
            switch['player_id'] for switch in switches
        }
        return self.strip_id(
            self.db.player.find({'id': {'$in': [pid for pid in player_ids]}}))

    def get_match_metadata(self, match_guid):
        res = self.db.match.find_one({'match_guid': match_guid})
        return self.strip_id(res)

    def get_team_lifecycle(self, match_guid):
        res = self.db.team_switch.find({'match_guid': match_guid})
        return self.strip_id(res)

    def get_player(self, player_id):
        res = self.db.player.find_one({'id': player_id})
        return self.strip_id(res)

    def get_match_scores(self, match_guid):
        res = self.db.score.find({'match_guid': match_guid})
        return self.strip_id(res)

    def get_match_special_scores(self, match_guid):
        res = self.db.special_score.find({'match_guid': match_guid})
        return self.strip_id(res)

    def get_match_kills(self, match_guid):
        res = self.db.kill.find({'match_guid': match_guid})
        return self.strip_id(res)

    def get_match_badges(self, match_guid):
        res = self.db.badge.find({'match_guid': match_guid})
        return self.strip_id(res)

    def get_players(self):
        return self.strip_id(self.db.player.find())

    def get_badge_sum(self):
        res = self.db.badge.aggregate([{
            '$group': {
                '_id': {'name': '$name', 'player_id': '$player_id'},
                'count': {'$sum': '$count'},
            }
        }])
        return [{
            'name': entry['_id']['name'],
            'player_id': entry['_id']['player_id'],
            'count': entry['count']} for entry in res]

    def get_total_stats(self):
        kills = self.db.kill.aggregate([{
            '$group': {
                '_id': {'killer_id': '$killer_id'},
                'count': {'$sum': 1}
            }
        }])
        deaths = self.db.kill.aggregate([{
            '$group': {
                '_id': {'victim_id': '$victim_id'},
                'count': {'$sum': 1}
            }
        }])
        return {
            'kills': [{
                'player_id': entry['_id']['killer_id'],
                'total': entry['count']
            } for entry in kills if entry['count'] > 100],
            'deaths': [{
                'player_id': entry['_id']['victim_id'],
                'total': entry['count']
            } for entry in deaths if entry['count'] > 100],
        }

    def get_map_stats(self):
        stats = self.db.match.aggregate([{
            '$group': {
                '_id': {'map_name': '$map_name'},
                'count': {'$sum': 1}
            }
        }])
        maps = {
            entry['map_name']: entry['size']
            for entry in self.db.map.find()
        }
        return [{
            'map_name': entry['_id']['map_name'],
            'size': maps.get(entry['_id']['map_name'], None),
            'count': entry['count']} for entry in stats]

    def prepare_for_rebuild(self):
        """
        Should drop all match related collections
        """
        skip = ['user']
        for name in self.db.list_collection_names():
            if name in skip:
                continue
            self.db.drop_collection(name)

    def get_user(self, username):
        return self.db.user.find_one({'username': username})

    def set_map_size(self, map_name, size):
        self.db.map.update(
            {'map_name': map_name}, {'map_name': map_name, 'size': size},
            upsert=True)
