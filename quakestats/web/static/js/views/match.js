// helper class storing players
class PlayersState {
    constructor() {
        riot.observable(this)
        this.players = {}
        this.focused = null
    }

    setPlayers(players) {
        this.players = players

        var colorHash = new ColorHash({
            saturation: 0.9,
            lightness: [0.5, 0.6, 0.65],
        })

        for (let player of Object.values(this.players)) {
            player.color = colorHash.hsl(player.id)
        }
    }

    getPlayerColor(playerId) {
        var color = this.getPlayer(playerId).color
        return `hsl(${color[0]}, ${color[1]}, ${color[2]})`
    }

    getPlayer(playerId) {
        return this.players[playerId]
    }

    setFocus(playerId) {
        this.focused = playerId
        this.trigger('player_focused', playerId)
    }
}

class MatchView {
    constructor(app, matchGuid) {
        this.matchGuid = matchGuid
        this.app = app
        this.gui = {}
        this.players = {}
    }

    run() {
        this.gui.weaponStats = riot.mount('weapon-stats', { loading: true })[0]

        Promise.all([this.fetch_players])
            .then(resolution => {
                var players = resolution[0]
                for (let player of players) {
                    this.players[player.id] = player
                }
            })

        // fixme, howto combine promises with view object
        Promise.all([this.fetch_match_player_stats, this.fetch_match_kills, this.fetch_players])
            .then(resolution => {
                var r_stats = resolution[0]
                var r_kills = resolution[1]
                this.setWeaponStats(r_stats, r_kills)
            })
    }

    // r_ - raw_
    setWeaponStats(r_stats, r_kills) {
        // need to calculate all weapons (from kills + from weapon stats)
        var finalStats = {}

        // calculate deaths and kills per player per weapon
        _.forEach(r_kills, (kill) => {
            var weaponName = _.get(this.app.resources.weaponMap, kill.by, kill.by)
                // ignore self kills, process world kills
            if (kill.killer_id != kill.victim_id) {
                // sum kills
                var path = `${kill.killer_id}.stats.${weaponName}.kills`
                _.set(finalStats, path, _.get(finalStats, path, 0) + 1)

                // sum deaths
                path = `${kill.victim_id}.stats.${weaponName}.deaths`
                _.set(finalStats, path, _.get(finalStats, path, 0) + 1)
            }
        })

        _.forEach(finalStats, (value, player_id) => {
            // add accuracy info from weapon stats
            var weaponStat = _.find(r_stats, { 'player_id': player_id })
            _.forEach(value.stats, (ws, wname) => {
                ws.hits = _.get(weaponStat, `weapons.${wname}.H`, null)
                ws.shots = _.get(weaponStat, `weapons.${wname}.S`, null)
            })
            value.player_id = player_id
            value.player = this.players[player_id]
        })
        this.gui.weaponStats.update({
            opts: {
                loading: false,
                players: this.players,
                stats: _.values(finalStats)
            }
        })
    }
}