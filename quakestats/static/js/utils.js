function datefmt(d) {
  var H = d.getHours()
  var m = d.getMinutes()
  var D = d.getDate()
  var M = d.getMonth() + 1  // Fuck you JS
  var Y = d.getFullYear()

  return `${Y}-${M}-${D} ${H}:${m}`
}

function isSelfKill(kill) {
  return (kill.killer_id == kill.victim_id) || (kill.killer_id == 'q3-world')
}

function kdrOverTime(kills, players) {
  var state = {}
  var traces = new Map()
  for (player of Object.values(players)) {
    state[player.id] = {k: 1, d: 1, r: 0} // each player starts with KDR=1 - 1
    traces.set(player.id, {
      x: [],
      y: [],
      name: player.name})
  }

  for (kill of kills) {
    if (!isSelfKill(kill)) {
      var player_state = state[kill.killer_id]
      player_state.k++;
      player_state.r = (Math.round(1000 * (player_state.k / player_state.d)) / 1000) - 1

      var trace = traces.get(kill.killer_id)
      trace.x.push(kill.game_time)
      trace.y.push(player_state.r)
    }

    var victim_state = state[kill.victim_id]
    victim_state.d++;
    victim_state.r = (Math.round(1000 * (victim_state.k / victim_state.d).toFixed(3)) / 1000) - 1

    var trace = traces.get(kill.victim_id)
    trace.x.push(kill.game_time)
    trace.y.push(victim_state.r)
  }
  return [state, traces]

}

function range(n) {
  return Array.from(Array(n).keys())
}
