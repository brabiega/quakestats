<smart-player-name>
    <span class={focused: this.focused, clickable: true} click={handleClick}>{getPlayerName()}</span>

    <style>
        @keyframes pulse {
            0%      { color: black }
            80%     { color: black }
            90%     { color: #ff9898 }
            100%    { color: black }
        }
        .focused {
            text-shadow: 0px 1px 1px red;
            animation-name: pulse;
            animation-duration: 2s;
            animation-iteration-count: infinite;
        }

        .clickable {
            cursor: pointer;
        }

        .clickable:hover {
            text-shadow: 1px 1px #2c9198;
        }
    </style>
    this.id = opts.id
    this.players = opts.players
    this.focused = false

    getPlayerName() {
        return this.players.getPlayer(this.id).name
    }

    this.players.on('player_focused', (player_id) => {
        if (this.id == player_id) {
            this.focused = true
        } else {
            this.focused = false
        }
        this.update()
    })

    handleClick(event) {
        this.players.setFocus(this.id)
    }

</smart-player-name>

<presence-list>
    <h4>Presence list based on latest 90 matches</h4>
    <table>
        <tr>
            <th>Name</th>
            <th>Games</th>
        </tr>
        <tr each={player in opts.players}>
            <td>{player.name}</td>
            <td>{opts.presence[player.id]}</td>
        </tr>
    </table>

    <style>
        table {
            width: auto;
        }

        td {
            padding: 2px 15px;
        }

        tr:hover {
            background-color: #e1e8ea;
        }
    </style>
</presence-list>