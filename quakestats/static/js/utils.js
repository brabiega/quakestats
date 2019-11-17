// this 'module' should be removed, it's bad to have util/tool module
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

  function initPlayer(playerId) {
    let player = players[playerId]
    state[player.id] = {k: 1, d: 1, r: 0} // each player starts with KDR=1 - 1
    traces.set(player.id, {
      x: [],
      y: [],
      name: player.name})
    return state[player.id]
  }

  for (kill of kills) {
    var killer_state = state[kill.killer_id]
    var victim_state = state[kill.victim_id]

    if (victim_state == undefined) {victim_state = initPlayer(kill.victim_id)}
    if (killer_state == undefined) {killer_state = initPlayer(kill.killer_id)}

    if (!isSelfKill(kill)) {
      killer_state.k++;
      killer_state.r = (Math.round(1000 * (killer_state.k / killer_state.d)) / 1000) - 1

      var trace = traces.get(kill.killer_id)
      trace.x.push(kill.game_time)
      trace.y.push(killer_state.r)
    }
    
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

function close_popups() {
  document.getElementsByClassName('popup')[0].remove()
  document.getElementsByClassName('popup-cover')[0].remove()
}

function create_popup() {
  var popup_cover = document.createElement('div')
  popup_cover.classList.add('popup-cover')
  popup_cover.onclick = close_popups
  var popup = document.createElement('div')
  popup.classList.add('popup')
  document.body.appendChild(popup_cover)
  return popup
}
