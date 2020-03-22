/*
    requires wretch

    TODO all the api calls should be made using wretch
*/
class QuakeStatsApi {
    constructor() {
        this.endpoint = '/api/v2'
        this.api = wretch('/api/v2')
    }

    get(path) {
        var req = new Request(`${this.endpoint}/${path}`)
        return fetch(req).then(function(response) {
            return response.json().then(function(json) {
                return json
            })
        })
    }

    getMatches() {
        return this.get('matches')
    }

    getAllMatches() {
        return this.get('matches/all')
    }

    getMatch(matchId) {
        return this.get(`match/${matchId}/metadata`)
    }

    getMatchPlayers(matchId) {
        return this.get(`match/${matchId}/players`)
    }

    getMatchScores(matchId) {
        return this.get(`match/${matchId}/score`)
    }

    getMatchTeams(matchId) {
        return this.get(`match/${matchId}/teams`)
    }

    getMatchSpecial(matchId) {
        return this.get(`match/${matchId}/special`)
    }

    getMatchKills(matchId) {
        return this.get(`match/${matchId}/kill`)
    }

    getMatchBadges(matchId) {
        return this.get(`match/${matchId}/badge`)
    }

    getMatchPlayerStats(matchId) {
        return this.get(`match/${matchId}/player_stats`)
    }

    getBoardBadges(lastNMatches) {
        if (lastNMatches) {
            return this.get(`board/badges?latest=${lastNMatches}`)
        } else {
            return this.get(`board/badges`)
        }
    }

    getAllPlayers() {
        return this.get(`players`)
    }

    getTotalStats(lastNMatches) {
        if (lastNMatches) {
            return this.get(`board/total?latest=${lastNMatches}`)
        } else {
            return this.get(`board/total`)
        }
    }

    getMaps() {
        return this.get(`maps`)
    }

    setMapInfo(map_name, info) {
        var headers = new Headers()
        headers.set('Content-type', 'application/json')
        var req = new Request(
            `${this.endpoint}/map/size`, {
                method: 'POST',
                credentials: 'include',
                headers: headers,
                body: JSON.stringify({
                    map_name: map_name,
                    size: info.size,
                    rate: info.rate
                })
            })
        fetch(req)
    }

    getPlayerKills(playerId) {
        return this.get(`player/${playerId}/kills`)
    }

    getPlayerDeaths(playerId) {
        return this.get(`player/${playerId}/deaths`)
    }
    getPlayerDeaths(playerId) {
        return this.get(`player/${playerId}/deaths`)
    }
    getPlayerBadges(playerId) {
        return this.get(`player/${playerId}/badges`)
    }

    getPlayer(playerId) {
        return this.get(`player/${playerId}`)
    }

    getPresenceList(matchCount) {
        return this.api.url(`/presence/${matchCount}`).get()
    }
}

class QuakeStatsDataProcessor {
    constructor() {}

    playersMap(apiResponse) {
        // converts [{id: 123, name: 'test'}] to {123: {id: 123, name: 'test'}}
        return apiResponse.reduce((val, entry) => { val[entry.id] = entry; return val }, {})
    }
}