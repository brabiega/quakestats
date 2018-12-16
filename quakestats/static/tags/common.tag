<smart-player-name>
    <span class={focused: this.focused, clickable: true} click={handleClick}>{getPlayerName()}</span>

    <style>
        .focused {
            color: #2c9198;
            text-shadow: 1px 1px #b7f2ef;
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