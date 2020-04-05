// not 100% sure how to organize gui code...
// I don't want to create entire js build pipeline...
// this should be fairly simple but powerfull
class Application {
    constructor(resources, view) {
        this.resources = resources
        this.view = view
    }

    run() {
        riot.compile(() => {
            this.view.run()
        })
    }

    setView(view) {
        this.view = view
    }
}