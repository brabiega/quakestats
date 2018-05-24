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
  <h4>Latest matches</h4>
  <table>
    <tr each={opts.matches}>
      <td>
        <a href="{this.link}">{ opts.datefmt(new Date(this.start_date)) }</a>
      </td>
      <td>{this.map_name}</td>
    </tr>
  </table>
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

<match-score-chart>
  <h4>Player scores</h4>
  <div id='score-chart'></div>
  
  this.on('mount', function() {
    Plotly.newPlot(
      'score-chart',
      opts.series,
      {
        'height': 600,
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: {b: 25, t: 25},
        hovermode: 'closest'
      })
  })
  
</match-score-chart>

<match-kills-chart>
  <h4>Player kills</h4>
  <div id='kill-chart'></div>
  
  this.on('mount', function() {
    Plotly.newPlot(
      'kill-chart',
      opts.series,
      {
        'height': 600,
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: {b: 25, t: 25, l: 20, r: 10},
        legend: {"orientation": "h"},
        hovermode: 'closest'
      })
  })
  
</match-kills-chart>
<match-deaths-chart>
  <h4>Player deaths</h4>
  <div id='death-chart'></div>
  
  this.on('mount', function() {
    Plotly.newPlot(
      'death-chart',
      opts.series,
      {
        'height': 600,
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: {b: 25, t: 25, l: 15, r: 10},
        legend: {"orientation": "h"},
        hovermode: 'closest'
      })
  })
  
</match-deaths-chart>

<score-summary>
  <h4>Final scores</h4>
  <table class='top3'>
    <tr>
      <th>Name</th>
      <th>Final score</th>
      <th>Fav weapon</th>
    </tr>
    <tr each={opts.scores}>
      <td>{opts.players[player_id].name}</td>
      <td>{score}</td>
      <td style="text-align:center">
        <img if={context.resources.weapons[fav_weapon]} src="{context.resources.weapons[fav_weapon].img}" class="fav-weapon"></img>
        <span if={!context.resources.weapons[fav_weapon]}>{fav_weapon}</span></td>
    </tr>
  </table>
</score-summary>

<team-switches>
  <h4>Team switches</h4>
  <table>
    <tr each={opts.switches}>
      <td>{this.game_time}</td>
      <td>{ context.players[this.player_id].name }</td>
      <td>{this.to}</td>
    </tr>
  </table>
</team-switches>

<special-scores>
  <h4>Special scores</h4>
  <div class="special-score-container">
    <div each={opts.specials}>
      <table>
        <tr>
          <th>{context.resources.badges.getInfo(this.key).name} <span class="hint-mark" data={this.key} onclick={info}>[?]</span></th>
          <th><img class="badge-img" src={context.resources.badges.getInfo(this.key).img}></img></th>
        </tr>
        <tr medal-class={this.parent.key} onclick={detail} each={sorted(this.values)} style="cursor: pointer">
          <td>{context.players[this.key].name}</td>
          <td>
            <span>{this.value.total}</span>
          </td>
        </tr>
      </table>
    </div>
  </div>

  sorted(scores) {
    return scores.sort(
      function(a, b) {
        return b.value.total - a.value.total || b.value.timestamp - a.value.timestamp
      }
    )
  }

  detail(e) {
    // TODO rename medal to badge
    var popup = create_popup()
    e.target.parentElement.insertAdjacentElement('afterend', popup)
    var medal = e.target.parentNode.getAttribute('medal-class')
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
  <table>
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
  <table>
    <tr>
      <th>Player</th>
      <th>Enemy</th>
      <th>Deaths</th>
      <th>% of total</th>
    </tr>
    <tr each={this.worst_enemies}>
      <td>{this.me}</td>
      <td>{this.enemy}</td>
      <td>{this.kills}</td>
      <td>{Math.round(this.total_pct)}%</td>
    </tr>
  </table>

  this.on('before-mount', () => {
    var players = this.opts.players
    var worst_enemy = d3.nest().key(function(d) {return d.victim_id})
    .key(function(d) {return d.killer_id})
    .rollup(function(e) {return e.length})
    .entries(this.opts.kills)

    worst_enemy = worst_enemy.map(
        (e) => {return {
          key: players[e.key].name,
          total: d3.sum(e.values, (e) => {return e.value}),
          values: e.values[d3.scan(e.values, (a, b) => {return b.value - a.value})]
        }})
    .sort((a, b) => {return a.key > b.key})
    worst_enemy = worst_enemy.map(
      (e) => {return {
        me: e.key,
        enemy: players[e.values.key].name,
        total: e.total,
        total_pct: (e.values.value / e.total) * 100,
        kills: e.values.value}})

    this.worst_enemies = worst_enemy.sort((a, b) => {return a.me.localeCompare(b.me)})
  })
</worst-enemy>

<kdr-chart>
  <h4>Kill/Death ratio</h4>
  <div id='kdr-chart'></div>

  this.on('before-mount', () => {
    var kdr = kdrOverTime(opts.kills, opts.players)
    var kdr_state = kdr[0]
    var kdr_chart = {
      x: [],
      y: [],
      type: 'bar'
    }

    for(state of Object.entries(kdr_state).sort((a, b) => {return b[1].r - a[1].r})) {
      if (state[0] == 'q3-world') {continue}
      kdr_chart.x.push(context.players[state[0]].name),
      kdr_chart.y.push(state[1].r)
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
        margin: {b: 25, t: 25},
      }
    )
  })
</kdr-chart>

<match-kdr-chart>
  <h4>Kill/Death ratio over time</h4>
  <div id='kdr-over-time-chart'></div>

  this.on('before-mount', () => {
    var kdr = kdrOverTime(opts.kills, opts.players)
    var kdr_traces = kdr[1]
    for (trace of kdr_traces.values()) {
      trace.type = 'scatter'
      trace.mode = 'lines+markers'
    }
    this.kdr_traces = kdr_traces
  })

  this.on('mount', () => {
    Plotly.newPlot(
      'kdr-over-time-chart',
      Array.from(this.kdr_traces.values()),
      {
        height: 400,
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: {b: 25, t: 25},
        hovermode: 'closest'
      }
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
          <img each={range(count)} class="badge-board-img" src={context.resources.badges.getInfo(key).img} title={context.resources.badges.getInfo(key).desc}></img>
        </div>
        <span class="badge-board-player-container">{opts.players[player_id].name}</span>
      </div>
    </div>
  </div>
  <div style="grid-column: 4 / -1; display: grid; grid-template-columns: repeat(6, 1fr)">
    <div each={opts.multibadges}>
      <div each={values} style="display: grid; grid-template-columns: repeat(4, 1fr)">
        <div class="badge-board-img-container">
          <img each={range(count)} class="badge-board-img" src={context.resources.badges.getInfo(key).img} title={context.resources.badges.getInfo(key).desc}></img>
        </div>
        <span class="badge-board-player-container">{opts.players[player_id].name}</span>
      </div>
    </div>
  </div>
  </div>
</match-badges>

<board-badges>
  <h4>Badge stats</h4>
  <table class='board-badges-table' style='text-align: center; border-collapse: collapse;'>
    <tr>
      <td>Player</td>
      <td each={opts.badgeres.getMedalNames()}>
        <img class="badge-board-img" src={opts.badgeres.getInfo(name).img} title={opts.badgeres.getInfo(name).desc}></img>
      </td>
    </tr>
    <tr each={opts.badges}>
      <td nowrap>{opts.players[this.player_id].name}</td>
      <td each={opts.badgeres.getMedalNames()} style={getStyle(name, this.badges[name])}>
        {this.badges[name]}
      </td>

    </tr>
  </table>

  <style>
    .board-badges-table tr:hover {
      border-top: 1px solid red;
      border-bottom: 1px solid red;
    }
  </style>

  getStyle(name, count) {
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
</board-badges>

<total-chart>
  <h4>Total {opts.type}</h4>
  <div id='total-{opts.type}-chart'></div>

  build_traces() {
    var data = this.opts.data.sort((a, b) => {return a.total - b.total})
    var traces = data.reduce(
      (previous, current) => {
        previous.y.push(context.players[current.player_id].name);
        previous.x.push(current.total);
        return previous},
      {x: [], y: []})
    return traces
  }

  this.on('mount', () => {
    var traces = this.build_traces()
    traces['type'] = 'bar'
    traces['orientation'] = 'h'
    Plotly.newPlot(
      `total-${this.opts.type}-chart`,
      [traces],
      {
        height: 25 * traces.y.length,
        margin: {b: 25, t: 25, l: 100, r: 25},
      }
    )
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
  <h4>Weapon Kills</h4>
  <table>
    <tr>
      <th>Player</th>
      <th each={weapon in opts.weapons}>
          <img if={context.resources.weapons[weapon]} src="{context.resources.weapons[weapon].img}" class="fav-weapon"></img>
          <span if={!context.resources.weapons[weapon]}>{weapon}</span></td>
      </th>
    </tr>
    <tr each={player_id in Object.keys(opts.player_weapon_kills)}>
      <td style="text-align: left">{opts.players[player_id].name}</td>
      <td each={weapon in opts.weapons}>
        {opts.player_weapon_kills[player_id][weapon] || 0}
      </td>
    </tr>
  </table>

  <style>
    td {
      text-align: center;
    }
  </style>
</weapon-kills>
