"""
TODO add documentation
"""
import pymongo
from copy import deepcopy


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
        self.store_player_stats(analysis_report)
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

        rows = self.db.player_merge.find({
            'src_player_id': src_player_id,
            'target_player_id': target_player_id
        })

        if not list(rows):
            self.db.player_merge.insert_one({
                'src_player_id': src_player_id,
                'target_player_id': target_player_id
            })

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
                    'killer_id': score[1],
                    # TODO rename killer_id to scorer_id
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

    def store_player_stats(self, analysis_report):
        # its possible that weapon stats is empty
        # not sure when it happens but I've seen such match
        if not analysis_report.player_stats:
            return

        match_guid = analysis_report.match_metadata.match_guid
        results = []
        for entry in analysis_report.player_stats:
            res = deepcopy(entry)
            res['match_guid'] = match_guid
            results.append(res)

        self.db.player_stats.insert_many(results)

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

    def get_matches(self, latest=None, raw=False):
        if latest:
            result = self.db.match.find().sort(
                'start_date', pymongo.DESCENDING).limit(latest)
        else:
            result = self.db.match.find()
        
        if raw:
            return result

        return self.strip_id(result)

    def get_match_participants(self, match_guids):
        switches = self.db.team_switch.find({'match_guid': {"$in": match_guids}})
        result = {
            guid: set()
            for guid in match_guids
        }

        for switch in switches:
            result[switch['match_guid']].add(switch['player_id'])

        return result

    def get_match_players(self, match_guid):
        player_ids = self.get_match_participants([match_guid])[match_guid]
        return self.get_players(ids=list(player_ids))

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

    def get_match_player_stats(self, match_guid):
        res = self.db.player_stats.find({'match_guid': match_guid})
        return self.strip_id(res)

    def get_players(self, ids=None):
        if ids:
            return self.strip_id(
                self.db.player.find(
                    {"id": {"$in": ids}}
                )
            )
        else:
            return self.strip_id(self.db.player.find())

    def get_badge_sum(self, latest=None):
        if latest:
            matches = self.get_matches(latest, True)
            aggregate = [
                {
                    '$match': {'match_guid': {'$in': [m['match_guid'] for m in matches]}}
                },
            ]
        else:
            aggregate = []

        aggregate.append(
            {
                '$group': {
                    '_id': {'name': '$name', 'player_id': '$player_id'},
                    'count': {'$sum': '$count'},
                }
            }
        )
        
        res = self.db.badge.aggregate(aggregate)
        return [{
            'name': entry['_id']['name'],
            'player_id': entry['_id']['player_id'],
            'count': entry['count']} for entry in res]

    def get_total_stats(self, latest=None):
        if latest:
            matches = self.get_matches(latest, True)
            match = {'match_guid': {'$in': [m['match_guid'] for m in matches]}}
            min_score = 0
        else:
            match = {}
            min_score = 100

        kills = self.db.kill.aggregate([
            {
                '$match': match},
            {
                '$group': {
                    '_id': {'killer_id': '$killer_id'},
                    'count': {'$sum': 1}
                }
            }
        ])
        deaths = self.db.kill.aggregate([
            {
                '$match': match
            },
            {
                '$group': {
                    '_id': {'victim_id': '$victim_id'},
                    'count': {'$sum': 1}
                }
            }
        ])
        return {
            'kills': [{
                'player_id': entry['_id']['killer_id'],
                'total': entry['count']
            } for entry in kills if entry['count'] > min_score],
            'deaths': [{
                'player_id': entry['_id']['victim_id'],
                'total': entry['count']
            } for entry in deaths if entry['count'] > min_score],
        }

    def get_map_stats(self):
        stats = self.db.match.aggregate([{
            '$group': {
                '_id': {'map_name': '$map_name'},
                'count': {'$sum': 1}
            }
        }])

        maps = {
            entry['map_name']: {
                'size': entry.get('size', None),
                'rate': entry.get('rate', None),
            }
            for entry in self.db.map.find()
        }

        result = []
        for entry in stats:
            map_name = entry['_id']['map_name']
            info = {
                'map_name': map_name,
                'count': entry['count'],
            }
            if map_name in maps:
                info.update({
                    'size': maps[map_name]['size'],
                    'rate': maps[map_name]['rate'],
                })
            result.append(info)
        return result

    def prepare_for_rebuild(self):
        """
        Should drop all match related collections
        """
        skip = ['user', 'map', 'player_merge']
        for name in self.db.list_collection_names():
            if name in skip:
                continue
            self.db.drop_collection(name)

    def post_rebuild(self):
        for merge in self.db.player_merge.find():
            self.merge_players(
                merge['src_player_id'],
                merge['target_player_id'])

    def get_user(self, username):
        return self.db.user.find_one({'username': username})

    def set_map_info(self, map_name, size=None, rate=None):
        info = {
            'map_name': map_name
        }
        if size:
            info['size'] = size
        if rate:
            info['rate'] = rate

        self.db.map.update(
            {'map_name': map_name},
            {'$set': info}, upsert=True)

    def drop_match_info(self, match_guid):
        skip = ['user', 'map', 'player_merge']
        for name in self.db.list_collection_names():
            if name in skip:
                continue
            c = pymongo.collection.Collection(self.db, name)
            c.delete_many({"match_guid": match_guid})

    def get_player_kills(self, player_id):
        res = self.db.kill.find({'killer_id': player_id})
        return self.strip_id(res or [])

    def get_player_deaths(self, player_id):
        res = self.db.kill.find({'victim_id': player_id})
        return self.strip_id(res or [])

    def get_player_badges(self, player_id):
        res = (
            self.db.badge.aggregate([
                {
                    '$match': {
                        'player_id': player_id,
                    }
                },
                {
                    '$group': {
                        '_id': {'name': '$name', 'player_id': '$player_id'},
                        'count': {'$sum': '$count'},
                    }
                }
            ])
        )
        return [{
            'name': entry['_id']['name'],
            'count': entry['count']} for entry in res]
