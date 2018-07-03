<player-weapons>
  <h4>Kills by weapon</h4>
  <div style="display: grid; grid-template-columns: repeat(6, 1fr)">
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

<player-info>
  <h4>Player info</h4>
  <span class="fancyfont">Nickname: {opts.info.name}</span>

  <style>
    .fancyfont {
      font-family: 'Wallpoet';
      font-size: 46px
    }
  </style>
</player-info>

<player-kdr>
  <h4>Total kills/deaths</h4>
  <div style="text-align:center">
    <span style="margin-right: 50px; color: green" class="fancyfont">kills {opts.kill_count}</span>
    <span style="margin-left: 50px; color: red" class="fancyfont">{opts.death_count} deaths</span>
  </div>

  <style>
    .fancyfont {
      font-family: 'Wallpoet';
      font-size: 46px
    }
  </style>
</player-kdr>
