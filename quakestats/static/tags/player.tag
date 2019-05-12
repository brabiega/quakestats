<player-weapons>
  <h4 style={"visibility: hidden": context.printable}>Kills by weapon</h4>
  <div style="display: grid; grid-template-columns: repeat(4, 1fr)">
    <div each={opts.kills_by_weapon}>
        <img if={context.resources.weapons[key]} src="{context.resources.weapons[key].img}" class="weapon-img"></img>
        <span if={!context.resources.weapons[key]}>{key}</span>
        <span style="font-family: 'Wallpoet'; font-size: 46px"> x {value}</span>

    </div>
  </div>

  <style>
    .weapon-img {
      height: 56px;
      padding: 1px;
    }
  </style>

</player-weapons>

<player-badges>
  <h4 style={"visibility: hidden": context.printable}>Badges</h4>
  <div style="display: grid; grid-template-columns: repeat(4, 1fr)">
    <div each={opts.badges}>
        <img if={context.resources.badges.getInfo(name).img} src="{context.resources.badges.getInfo(name).img}" class="weapon-img"></img>
        <span if={!context.resources.badges.getInfo(name).img}>{name}</span>
        <span style="font-family: 'Wallpoet'; font-size: 46px"> x {count}</span>

    </div>
  </div>

  <style>
    .weapon-img {
      height: 56px;
      padding: 1px;
    }
  </style>

</player-badges>

<player-info>
  <h4 style={"visibility: hidden": context.printable}>Player info</h4>
  <span class="fancyfont">Nickname: {opts.info.name}</span>
  <span style="float: right;" class="fancyfont">Total games: {opts.total_games}</span>

  <style>
    .fancyfont {
      font-family: 'Wallpoet';
      font-size: 46px
    }
  </style>
</player-info>

<player-kdr>
  <h4 style={"visibility: hidden": context.printable}>Total kills/deaths</h4>
  <div style="display: grid; grid-template-columns: repeat(2, 1fr); grid-column-gap:30px">
      <span style="color: green; text-align: right" class="fancyfont">kills {opts.kill_count}</span>
      <span style="color: red" class="fancyfont">{opts.death_count} deaths</span>
  </div>

  <style>
    .fancyfont {
      font-family: 'Wallpoet';
      font-size: 46px
    }
  </style>
</player-kdr>

<player-top-target>
  <h4 style={"visibility: hidden": context.printable}>Top 0x10 targets</h4>
  <table>
    <tr each={opts.targets}>
      <td style="text-align: right" class="fancyfont">{opts.players[key].name}</td>
      <td style='color: green; text-align: center' class="fancyfont">{value}</td>
    </tr>
  </table>

  <style>
    .fancyfont {
      font-family: 'Wallpoet';
      font-size: 24px
    }
  </style>

</player-top-target>

<player-top-enemy>
  <h4 style={"visibility: hidden": context.printable}>Top 0x10 enemies</h4>
  <table>
    <tr each={opts.enemies}>
      <td style='color: red; text-align: center' class="fancyfont">{value}</td>
      <td class="fancyfont">{opts.players[key].name}</td>
    </tr>
  </table>

  <style>
    .fancyfont {
      font-family: 'Wallpoet';
      font-size: 24px
    }
  </style>

</player-top-enemy>
