<player-name>
  <span class="player-name">
    <font each="{opts.data}" style="color: {this[0]}">{this[1]}</font>
  </span>

  /*
    Example opts
    opts = [
      ['white', 'Player '],
      ['yellow', 'Name'],
    ]
  */
</player-name>

<player-list>
  <h4>Finished players</h4>
  <ul>
    <li each="{opts.data}">
      <player-name data="{this.colorized}"></player-name>
    </li>
  </ul>

  /*
    Example opts
    opts = [
      {
        name: "darek",
        colorized: [
          ['white', 'Player '],
          ['yellow', 'Name'],
        ],
      },
      {
        name: "marek",
        colorized: [
          ['red', 'TEst']
        ],
      }
    ]
  */

</player-list>

<match-list>
  <h4 style="margin-bottom: 0px">Latest matches</h4>
  <div style="display: grid; grid-template-columns: repeat(5, 1fr);">
    <div each={matchesChunk in chunk(opts.matches, 5)} style="text-align: center; padding: 4px;">
      <a each={match in matchesChunk} href="{match.link}" class='match-entry'>
        { opts.datefmt(new Date(match.start_date)) } | {match.map_name} | {match.game_type}
        <div>{this.describe(match)}</div>
      </a>
    </div>
  </div>

  <style>
  .match-entry {
    display: block;
    padding: 4px;
  }

  .match-entry:hover {
    display: block;
    background: #2c9198;
    color: white;
  }
  </style>

  describe(match) {
    if (!match.summary) {
      return ""
    }
    if (match.game_type == "DUEL") {
      let summary = match.summary
      let p1 = opts.players[summary.scores[0].player_id].name
      let p2 = opts.players[summary.scores[1].player_id].name
      return `${summary.scores[0].score} : ${summary.scores[1].score} | ${p1} : ${p2}`
    }
    return ""
  }

  chunk(arr, chunkSize) {
    var R = [];
    for (var i=0,len=arr.length; i<len; i+=chunkSize)
      R.push(arr.slice(i,i+chunkSize));
    return R;
  }
</match-list>

<match-info>
  <h4>Match info</h4>
  <table>
    <tr each={showprops}>
      <td>{name}</td>
      <td>{this.opts.match[prop]}</td>
    </tr>
  </table>

  this.showprops = [
    {prop: 'server_domain', name: 'Server domain'},
    {prop: 'server_name', name: 'Server name'},
    {prop: 'game_type', name: 'Game type'},
    {prop: 'map_name', name: 'Map name'},
    {prop: 'start_date', name: 'Start date'},
    {prop: 'finish_date', name: 'Finish date'},
    {prop: 'exit_message', name: 'Finish reason'},
    {prop: 'duration', name: 'Duration'},
    {prop: 'time_limit', name: 'Time limit'},
    {prop: 'frag_limit', name: 'Frag limit'},
    {prop: 'capture_limit', name: 'Capture limit'},
  ]
</match-info>

<duel-info>
  <span style="text-align: center">{this.opts.match.start_date} | {this.opts.match.map_name} | {this.opts.match.exit_message}</span>

  <style>
  span {
    text-align: center;
    font-size: 20px;
    font-weight: bold;
  }
  </style>
</duel-info>

<accuracy-info>
  <h4>Accuracy info</h4>
  <table>
    <tr>
      <td>Player</td>
      <td each={weapon in this.getWeapons(opts.stats)} style="text-align: center">
        <img if={context.resources.weapons[weapon]} src="{context.resources.weapons[weapon].img}" class="fav-weapon"></img>
      </td>
    </tr>
    <tr each={stat in opts.stats}>
      <td>{context.players[stat.player_id].name}</td>
      <td each={weapon in this.getWeapons(opts.stats)} class="acc-text">
        {calcAcc(stat.weapons[weapon])}
      </td>
    </tr>
  <table>

  <style>
    .acc-text {
      text-align: center;
      font-size: 10px;
    }
  </style>

  calcAcc(weaponStats) {
    if (!weaponStats) {
      return "-"
    }
    let hits = weaponStats.H
    let shots = weaponStats.S

    if (hits && shots) {
      return (100 * hits/shots).toFixed(2)
    } else {
      return "-"
    }
  }

  getWeapons(stats) {
    return _.uniq(_.flatten(stats.map(e => _.keys(e.weapons))))
  }

</accuracy-info>

<match-score-chart>
  <h4>Player scores</h4>
  <div id='score-chart'></div>
  
  this.series = opts.series
  this.specials_by_type = opts.specials_by_type
  this.scores = opts.scores
  this.match_info = opts.match_info
  this.max_score = opts.max_score

  var special_series = []
  var head_hunter = (this.specials_by_type['HEADHUNTER'] || []).map(
    (special) => {
      var score = this.scores.filter((e) => {
        return (
          e.game_time == special.game_time &&
          e.player_id == special.killer_id
        )
      })[0]
      return {
        x: score.game_time,
        y: score.score,
        victim_id: special.victim_id,
        killer_id: special.killer_id,
      }

    }
  ).reduce(
    (prev, cur) => {
      prev.x.push(cur.x)
      prev.y.push(cur.y)
      prev.hovertext.push(
        `${context.players[cur.killer_id].name} killed ${context.players[cur.victim_id].name}`
      )
      return prev
    },
    {
      x: [],
      y: [],
      hovertext: [],
      type: 'scatter',
      mode: 'markers',
      marker: {
        symbol: "star", size:16, color: "gold",
      },
      name: 'Headhunter',
    }
  )
  this.series.push(head_hunter)

  this.on('mount', function() {
    Plotly.newPlot(
      'score-chart',
      this.series,
      {
        'height': 600,
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: {b: 25, t: 25},
        hovermode: 'closest',
        shapes: [
          {
            type: 'line',
            x0: this.match_info.duration, y0: 0,
            x1: this.match_info.duration, y1: this.max_score,
            line: {
              color: '#ffc8c8',
              width: 1,
            }
          }
        ]
      }
    )
  })
  
</match-score-chart>

<match-kills-chart>
  <h4>Player kills</h4>
  <div id='kill-chart'></div>
  
  this.on('mount', function() {
    let layout = {
        'height': 600,
        margin: {b: 25, t: 25, l: 20, r: 10},
        legend: {"orientation": "h"},
        hovermode: 'closest'
    }

    if (this.opts.chartLayout) {
      layout = this.opts.chartLayout
    }

    Plotly.newPlot(
      'kill-chart',
      opts.series,
      layout,
    )
  })
  
</match-kills-chart>
<match-deaths-chart>
  <h4>Player deaths</h4>
  <div id='death-chart'></div>
  
  this.on('mount', function() {
    let layout = {
        'height': 600,
        margin: {b: 25, t: 25, l: 20, r: 10},
        legend: {"orientation": "h"},
        hovermode: 'closest'
    }

    if (this.opts.chartLayout) {
      layout = this.opts.chartLayout
    }

    Plotly.newPlot(
      'death-chart',
      opts.series,
      layout,
    )
  })
  
</match-deaths-chart>

<score-summary>
  <h4>Final scores</h4>
  <table class="top3 table-centered">
    <tr>
      <th>Name</th>
      <th>Final score</th>
      <th>Fav weapon</th>
    </tr>
    <tr each={opts.scores}>
      <td>
        <smart-player-name id={player_id} players={players}></smart-player-name>
      </td>
      <td>{score}</td>
      <td style="text-align:center">
        <img if={context.resources.weapons[fav_weapon]} src="{context.resources.weapons[fav_weapon].img}" class="fav-weapon"></img>
        <span if={!context.resources.weapons[fav_weapon]}>{fav_weapon}</span></td>
    </tr>
  </table>

  this.players = opts.players
</score-summary>

<team-switches>
  <h4>Team switches</h4>
  <table>
    <tr each={opts.switches}>
      <td>{this.game_time}</td>
      <td>
        <smart-player-name id={player_id} players={players}></smart-player-name>
      <td>{this.to}</td>
    </tr>
  </table>
  this.players = opts.players
</team-switches>

<special-scores>
  <h4>Special scores</h4>
  <div class="special-score-container">
    <div each={opts.specials}>
      <table class="table-centered">
        <tr>
          <th>{context.resources.badges.getInfo(this.key).name} <span class="hint-mark" data={this.key} onclick={info}>[?]</span></th>
          <th><img class="badge-img" src={context.resources.badges.getInfo(this.key).img}></img></th>
        </tr>
        <tr medal-class={this.parent.key} onclick={detail} each={sorted(this.values)} style="cursor: pointer">
          <td>
            <smart-player-name id={this.key} players={players}></smart-player-name>
          <td>
            <span>{this.value.total}</span>
          </td>
        </tr>
      </table>
    </div>
  </div>
  this.players = opts.players
  sorted(scores) {
    return scores.sort(
      function(a, b) {
        return b.value.total - a.value.total || b.value.timestamp - a.value.timestamp
      }
    )
  }

  detail(e) {
    // TODO rename medal to badge
    
    
    // TODO this is workaround-ish
    // need to traverse
    function findMedal(node) {
      if (!node) {
        return null
      }
      var medal = node.getAttribute('medal-class')
      if (medal) {
        return medal
      } else {
        return findMedal(node.parentNode)
      }
    }
    var medal = findMedal(e.target.parentElement)
    if (!medal) {return}

    var popup = create_popup()
    e.target.parentElement.insertAdjacentElement('afterend', popup)
    var details = this.opts.details.find(function (d) {return d.key==medal})
      .values.find(function(d) {return d.key==e.item.key})

    details = this.sorted(details.values).map(function(d)
      {return {player: context.players[d.key], value: d.value}})
    riot.mount(popup, 'special-score-details', {list: details})
  }

  info(e) {
    var popup = create_popup()
    e.target.parentElement.appendChild(popup)
    var medal_id = e.target.getAttribute('data')
    var medal_info = context.resources.badges.getInfo(medal_id)
    riot.mount(popup, 'special-score-info', {badge: medal_info})
  }
</special-scores>

<special-score-details>
  <table class="table-centered">
    <tr each={opts.list}>
      <td>{this.player.name}</td>
      <td>{this.value}</td>
    </tr>
  </table>
</special-score-details>

<special-score-info>
  <ul if={opts.badge} style="list-style: none; padding: 0px">
    <li><img class="badge-img" src={this.opts.badge.img}></img></li>
    <li>{this.opts.badge.name}</li>
    <li>{this.opts.badge.desc}</li>
  </ul>
  <span if={!opts.badge}>Click for details</span>
</special-score-info>

<worst-enemy>
  <h4>Worst enemy</h5>
  <table class="table-centered">
    <tr>
      <th>Player</th>
      <th>Enemy</th>
      <th>Deaths</th>
      <th>% of total</th>
    </tr>
    <tr each={this.worst_enemies}>
      <td>
        <smart-player-name id={me} players={players}></smart-player-name>
      </td>
      <td>
        <smart-player-name id={enemy} players={players}></smart-player-name>
      </td>
      <td>{this.kills}</td>
      <td>{Math.round(this.total_pct)}%</td>
    </tr>
  </table>
  
  this.players = opts.players
  this.on('before-mount', () => {
    var worst_enemy = d3.nest().key(function(d) {return d.victim_id})
    .key(function(d) {return d.killer_id})
    .rollup(function(e) {return e.length})
    .entries(this.opts.kills)

    worst_enemy = worst_enemy.map(
        (e) => {return {
          key: e.key,
          total: d3.sum(e.values, (e) => {return e.value}),
          values: e.values[d3.scan(e.values, (a, b) => {return b.value - a.value})]
        }})
    .sort((a, b) => {return a.key > b.key})
    worst_enemy = worst_enemy.map(
      (e) => {return {
        me: e.key,
        enemy: e.values.key,
        total: e.total,
        total_pct: (e.values.value / e.total) * 100,
        kills: e.values.value}})

    this.worst_enemies = worst_enemy.sort((a, b) => {return a.me.localeCompare(b.me)})
  })
</worst-enemy>

<kdr-chart>
  <h4>Kill/Death ratio</h4>
  <div id='kdr-chart'></div>

  this.players = opts.players

  this.on('before-mount', () => {
    var kdr = kdrOverTime(opts.kills, this.players.players)
    var kdr_state = kdr[0]
    var kdr_chart = {
      x: [],
      y: [],
      type: 'bar',
      marker: {color:[]},
    }

    for(state of Object.entries(kdr_state).sort((a, b) => {return b[1].r - a[1].r})) {
      if (state[0] == 'q3-world') {continue}
      kdr_chart.x.push(this.players.getPlayer(state[0]).name)
      kdr_chart.y.push(state[1].r)
      kdr_chart.marker.color.push(this.players.getPlayerColor(state[0]))
    }
    this.kdr_chart = kdr_chart
  })

  this.on('mount', () => {
    Plotly.newPlot(
      'kdr-chart',
      [this.kdr_chart],
      {
        height: 250,
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: {b: 25, t: 25, l: 25, r: 25},
      }
    )
  })
</kdr-chart>

<match-kdr-chart>
  <h4>Kill/Death ratio over time</h4>
  <div id='kdr-over-time-chart'></div>
  this.players = opts.players

  this.on('before-mount', () => {
    var kdr = kdrOverTime(opts.kills, this.players.players)
    var kdr_traces = kdr[1]
    for ([player_id, trace] of kdr_traces.entries()) {
      trace.type = 'scatter'
      trace.mode = 'lines+markers'
      trace.line = {color: this.players.getPlayerColor(player_id)}
    }
    this.kdr_traces = kdr_traces
  })

  this.on('mount', () => {
    let layout = {
        height: 400,
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: {b: 25, t: 25},
        hovermode: 'closest',
    }
    if (this.opts.chartLayout != undefined) {
      layout = this.opts.chartLayout
    }

    Plotly.newPlot(
      'kdr-over-time-chart',
      Array.from(this.kdr_traces.values()),
      layout,
    )
  })
</match-kdr-chart>

<match-badges>
<h4>Badges</h4>
  <div class="badges-container">
  <div style="grid-column: 1 / 4; display: grid; grid-template-columns: repeat(4, 1fr)">
    <div each={opts.singlebadges}>
      <div each={values} style="display: grid; grid-template-columns: repeat(4, 1fr)">
        <div class="badge-board-img-container">
          <img each={range(count)} class="badge-board-img" src={context.resources.badges.getInfo(key).img} title={context.resources.badges.getInfo(key).name + ': '+ context.resources.badges.getInfo(key).desc}></img>
        </div>
        <span class="badge-board-player-container">
          <smart-player-name id={player_id} players={players}></smart-player-name>
        </span>
      </div>
    </div>
  </div>
  <div style="grid-column: 4 / -1; display: grid; grid-template-columns: repeat(6, 1fr)">
    <div each={opts.multibadges}>
      <div each={values} style="display: grid; grid-template-columns: repeat(4, 1fr)">
        <div class="badge-board-img-container">
          <img each={range(count)} class="badge-board-img" src={context.resources.badges.getInfo(key).img} title={context.resources.badges.getInfo(key).desc}></img>
        </div>
        <span class="badge-board-player-container">
          <smart-player-name id={player_id} players={players}></smart-player-name>
        </span>
      </div>
    </div>
  </div>
  </div>
  this.players = opts.players
</match-badges>

<badge-img>
  <img
    class="badge-img"
    src={badgeCatalog.getInfo(this.name).img}
    title="{badgeCatalog.getInfo(this.name).name}: {badgeCatalog.getInfo(this.name).desc}">
  </img>

  <style>
    .badge-img {
      height: 48px;
    }
  </style>

  this.name = opts.name

  // reference to global object :/
  this.badgeCatalog = resources.badges
</badge-img>

<board-badges>
  <h4>
    Badge stats 
    | Last <a href="#" class={"selected": this.selected==10} onClick={fetch(10)}>10</a>
    | <a href="#" class={"selected": this.selected==30} onClick={fetch(30)}>30</a>
    | <a href="#" class={"selected": this.selected==60} onClick={fetch(60)}>60</a>
    | <a href="#" class={"selected": this.selected==90} onClick={fetch(90)}>90</a>
    | <a href="#" class={"selected": this.selected==150} onClick={fetch(150)}>150</a> matches 
    | <a href="#" class={"selected": this.selected==undefined} onClick={fetch()}>Total</a> (Top 20 / <a href="#" onclick={toggleShowAll}>Show all</a>)</h4>
  <table class='board-badges-table' style='text-align: center; border-collapse: collapse;'>
    <colgroup>
      <col style="width:10%">
    </colgroup>
    <thead>
      <tr>
        <th>Player</th>
        <th each={badgeName in firstBadges}>
          <badge-img name={badgeName}/>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr each={playerInfo in sortPlayers(firstBadges)}>
        <td nowrap>
          <a href="/player/{playerInfo.playerId}">{opts.players[playerInfo.playerId].name} ({playerInfo.sum})</a>
        </td>
        <td each={badgeName in firstBadges} class={getClass(badgeName, playerInfo.playerId)}>
          {
            this.badgesByPlayerByName[playerInfo.playerId][badgeName] &&
            this.badgesByPlayerByName[playerInfo.playerId][badgeName].count
          }
        </td>
      </tr>
    </tbody>
  </table>
  <hr>
  <table class='board-badges-table' style='text-align: center; border-collapse: collapse;'>
    <colgroup>
      <col style="width:10%">
    </colgroup>
    <thead>
      <tr>
        <th>Player</th>
        <th each={badgeName in secondBadges}>
          <badge-img name={badgeName}/>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr each={playerInfo in sortPlayers(secondBadges)}>
        <td nowrap>
          <a href="/player/{playerInfo.playerId}">{opts.players[playerInfo.playerId].name} ({playerInfo.sum})</a>
        </td>
        <td each={badgeName in secondBadges} class={getClass(badgeName, playerInfo.playerId)}>
          {
            this.badgesByPlayerByName[playerInfo.playerId][badgeName] &&
            this.badgesByPlayerByName[playerInfo.playerId][badgeName].count
          }
        </td>
      </tr>
    </tbody>
  </table>


  <style>
    .board-badges-table>tbody>tr:hover {
      background: #b7F2ef;
    }

    .gold {
      color: gold;
      font-weight: bold;
      text-shadow: 0px 1px 1px black;
    }

    .silver {
      color: silver;
      font-weight: bold;
      text-shadow: 0px 1px 1px black;
    }

    .bronze {
      color: #9d2b2b;
      font-weight: bold;
      text-shadow: 1px 1px 1px #777;
    }

    .almost {
      color: #ff8989;
      font-weight: bold;
      text-shadow: 1px 1px 1px black;
    }

    .selected {
      color: red;
    }
  </style>
  /* required opts are:
    badges:
      [{player_id, name, count}, ...]
    players:
      [{id, name}]

    Will display two tables consisting of two groups of badges
  */

  // global data
  this.badgeCatalog = resources.badges
  this.firstBadges = [
    'WIN_GOLD', 'WIN_SILVER', 'WIN_BRONZE', 'WIN_ALMOST', 'GAUNTLET_KILL', 'DEATH', 'KILLING_SPREE',
    'VENGEANCE'
  ]
  this.secondBadges = Object.keys(this.badgeCatalog.data).filter((e) => {return !this.firstBadges.includes(e)})
  this.showAll = false

  prepareData(badges) {
    this.badgesByPlayerByName = d3.nest()
      .key((d) => {return d.player_id})
      .key((d) => {return d.name})
      .rollup((v) => {return {'count': v[0].count}})
      .object(badges)

    this.badgesByNameByPlayer = d3.nest()
      .key((d) => {return d.name})
      .key((d) => {return d.player_id})
      .rollup((v) => {return {'count': v[0].count}})
      .object(badges)

    this.topBadgeCount = {}
    for (let badgeName in this.badgesByNameByPlayer) {
      let badgesByPlayer = this.badgesByNameByPlayer[badgeName]
      this.topBadgeCount[badgeName] = Array.from(new Set(Object.values(badgesByPlayer)
        .sort((a, b) => {return b.count - a.count})
        .map((e) => {return e.count})))
    }
  }

  sortPlayers(byBadges) {
    let result = []
    for (let playerId in this.badgesByPlayerByName) {
      let playerBadges = this.badgesByPlayerByName[playerId]
      let selectedBadges = d3.entries(playerBadges)
        .map((d) => {return {badgeName: d.key, count: d.value.count}})
        .filter((e) => {return byBadges.includes(e.badgeName)})
      let sum = d3.sum(selectedBadges, (e) => {return e.count})
      result.push({'playerId': playerId, 'sum': sum})
    }
    let res = result.sort((a, b) => {return b.sum - a.sum})
    if (!this.showAll) {
      return res.slice(0, 20)
    } else {
      return res
    }
  }

  this.on('mount', () => {
    this.fetchData(30)
  })

  fetchData(nLatest) {
    this.selected = nLatest
    var self = this
    opts.selectedNMatches.trigger('set', nLatest)
    qapi.getBoardBadges(nLatest).then((json) => {
      self.prepareData(json)
      if (nLatest) {
        self.showAll = true
      } else {
        self.showAll = false
      }
      self.update()
    })
  }

  fetch(nLatest) {
    return () => {
      this.fetchData(nLatest)
    }
  }

  getClass(badgeName, playerId) {
    if (
      (!this.badgesByPlayerByName[playerId]) ||
      (!this.badgesByPlayerByName[playerId][badgeName])
    ) {
      return {}
    }

    let badge = this.badgesByPlayerByName[playerId][badgeName]
    let topCount = this.topBadgeCount[badgeName]
    return {
      'gold': topCount[0] && topCount[0] == badge.count,
      'silver': topCount[1] && topCount[1] == badge.count,
      'bronze': topCount[2] && topCount[2] == badge.count,
      'almost': topCount[3] && topCount[3] == badge.count,
    }
  }

  getStyle(name, count) {
    // unused for now
    var color = 'hsl(183, 45%, 50%)'
    var max = this.opts.max_badges[name]
    if (count && max) {
      lightness = 100 - Math.round((count/max) * 50)
    } else {
      lightness = 100
    }
    var style = `background-color: hsl(183, 45%, ${lightness}%)`

    if ((count && max) && (count == max)) {
      style = `${style}; color: white; font-weight:bold`
    }
    return style
  }

  toggleShowAll(e) {
    this.showAll = true
    this.update()
  }
</board-badges>

<total-chart>
  <h4>Total {opts.type}</h4>
  <div id='total-{opts.type}-chart'></div>

  build_traces(rawData) {
    var data = rawData.sort((a, b) => {return a.total - b.total})
    var traces = data.reduce(
      (previous, current) => {
        previous.y.push(context.players[current.player_id].name);
        previous.x.push(current.total);
        return previous},
      {x: [], y: []})
    return traces
  }

  opts.stats.on('updated', () => {
    var traces = this.build_traces(opts.stats[opts.type])
    traces['type'] = 'bar'
    traces['orientation'] = 'h'
    Plotly.purge(`total-${this.opts.type}-chart`)
    Plotly.newPlot(
      `total-${this.opts.type}-chart`,
      [traces],
      {
        height: 25 * traces.y.length,
        margin: {b: 25, t: 25, l: 100, r: 25},
      }
    )
  })

  this.on('mount', () => {
  
  })

</total-chart>

<map-list>
  <table>
    <tr>
      <th>Games</th>
      <th>Map name</th>
      <th>Size</th>
      <th>Rate</th>
    </tr>
    <tr each={maps}>
      <td>{count}</td>
      <td>{map_name}</td>
      <td>{size}</td>
      <td>{rate}</td>
      <td if={context.user.role == 'admin'}>
        <span
          click={update_map_size} 
          each={map_size in this.map_sizes}
          class='map-size-btn'>{map_size}</span>
      </td>
      <td if={context.user.role == 'admin'}>
        <span
          click={update_map_rate}
          each={map_rate in this.map_rates}
          class='map-size-btn'>{map_rate}</span>
      </td>

    </tr>
  </table>

  <style>
    .map-size-btn {
      padding: 0px 10px;
      cursor: pointer;
    }
    .map-size-btn:hover {
      color: red;
    }
  </style>

  this.on('before-mount', () => {
    var data = this.opts.maps.sort((a, b) => {return a.count - b.count})
    this.maps = data
    this.map_sizes = ['S', 'M', 'L', 'XL']
    this.map_rates = [1, 2, 3, 4, 5]
  })

  update_map_size(e) {
    // bad design
    var tag = e.target._tag
    qapi.setMapInfo(
      tag.map_name,
      {'size': tag.map_size})
  }
  update_map_rate(e) {
    // bad design
    var tag = e.target._tag
    qapi.setMapInfo(
      tag.map_name,
      {'rate': tag.map_rate})
  }

</map-list>

<weapon-kills>
  <h4>Weapon Kills & Deaths</h4>
  <table>
    <tr>
      <th>Player</th>
      <th each={weapon in opts.weapons}>
          <img if={context.resources.weapons[weapon]} src="{context.resources.weapons[weapon].img}" class="fav-weapon"></img>
          <span if={!context.resources.weapons[weapon]}>{weapon}</span></td>
      </th>
    </tr>
    <tr each={player_id in Object.keys(opts.player_weapon_kills)}>
      <td style="text-align: left">
        <smart-player-name id={player_id} players={players}></smart-player-name>
      </td>
      <td each={weapon in opts.weapons}>
        <span style='color: green'>
          {opts.player_weapon_kills[player_id][weapon] && opts.player_weapon_kills[player_id][weapon]['kills'] || 0}
        </span>
        <span style='color: red'>
          {opts.player_weapon_kills[player_id][weapon] && opts.player_weapon_kills[player_id][weapon]['deaths'] || 0}
        </span>
      </td>
    </tr>
  </table>

  <style>
    td {text-align: center;}
  </style>

  this.players = this.opts.players
</weapon-kills>

<match-player-kill-death>
  <h4>Player kills/deaths details</h4>
  <div class="kill-death-details-container">
    <div class="detail-container" each={Object.entries(opts.kds)}>
      <table>
        <thead>
          <tr class="head">
            <th>{players.getPlayer(this[0]).name}</th>
            <th style="width:20%">K</th>
            <th style="width:20%">D</th>
          </tr>
        <thead>
        <tr each={Object.entries(this[1])}>
          <td>
            <smart-player-name id={this[0]} players={players}></smart-player-name>
          </td>
          <td class={better: this[1].kills > this[1].deaths}>{this[1].kills}</td>
          <td class={worse: this[1].deaths > this[1].kills}>{this[1].deaths}</td>
        </tr>
      </table>
    </div>
  </div>

  <style>
    .kill-death-details-container {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      grid-column-gap: 10px;
      grid-row-gap: 10px;
    }
    td {
      text-align: center;
    }
    .head {
      background-color: #2b9198;
      color: white;
    }
    .detail-container {
      border-style: solid;
      border-width: 1px;
      border-color: #2b9198;
    }
    .better {
      color: #2dc12d;
      font-weight: bold;
    }
    .worse {
      color: red;
      font-weight: bold;
    }
  </style>
  this.players = opts.players
</match-player-kill-death>

<player-damage-summary>
  <h4>Damage stats</h4>
  <div style="display: grid; grid-template-columns: repeat(2, 1fr)">
    <div ref="chartDealt"></div>
    <div ref="chartTaken"></div>
  </div>

  this.on('mount', () => {
    var dataDealt = [{
      values: this.damageDealt.map(e => {return e[1]}),
      labels: this.damageDealt.map(e => {return this.players.getPlayer(e[0]).name}),
      type: 'pie',
      textinfo: 'value',
      title: 'Damage dealt',
    }];
    Plotly.newPlot(
      this.refs.chartDealt,
      dataDealt,
      {
        height: 300,
        margin: {b: 25, t: 25, l: 25, r: 25},
      }
    )
    var dataTaken = [{
      values: this.damageTaken.map(e => {return e[1]}),
      labels: this.damageTaken.map(e => {return this.players.getPlayer(e[0]).name}),
      type: 'pie',
      textinfo: 'value',
      title: 'Damage taken',
    }];
    Plotly.newPlot(
      this.refs.chartTaken,
      dataTaken,
      {
        height: 300,
        margin: {b: 25, t: 25, l: 25, r: 25},
      }
    )
  })

  this.players = opts.players
  this.damageDealt = opts.damageDealt
  this.damageTaken = opts.damageTaken

</player-damage-summary>

<player-pickup-summary>
  <h4>Health and armor stats</h4>
  <div style="display: grid; grid-template-columns: repeat(2, 1fr)">
    <div ref="chartHealth"></div>
    <div ref="chartArmor"></div>
  </div>

  this.on('mount', () => {
    var dataHealth = [{
      values: this.totalHealth.map(e => {return e[1]}),
      labels: this.totalHealth.map(e => {return this.players.getPlayer(e[0]).name}),
      type: 'pie',
      textinfo: 'value',
      title: 'Health picked up',
    }];
    Plotly.newPlot(
      this.refs.chartHealth,
      dataHealth,
      {
        height: 300,
        margin: {b: 25, t: 25, l: 25, r: 25},
      }
    )
    var dataArmor = [{
      values: this.totalArmor.map(e => {return e[1]}),
      labels: this.totalArmor.map(e => {return this.players.getPlayer(e[0]).name}),
      type: 'pie',
      textinfo: 'value',
      title: 'Armor picked up',
    }];
    Plotly.newPlot(
      this.refs.chartArmor,
      dataArmor,
      {
        height: 300,
        margin: {b: 25, t: 25, l: 25, r: 25},
      }
    )
  })

  this.players = opts.players
  this.totalHealth = opts.totalHealth
  this.totalArmor = opts.totalArmor

</player-pickup-summary>

<duel-title>
  <div>
    <div class="duel-player" style="float: left">{this.opts.players[0]}</div>
    <div style="width: 20%; float: left; text-align: center">
      <img style="height: 164px" src="/static/img/vs.png"/>
    </div>
    <div class="duel-player" style="float: left;">{this.opts.players[1]}</div>
    <div style="text-align: center">
      <duel-info match={this.opts.matchInfo}></duel-info>
    </div>
  </div>
</duel-title>