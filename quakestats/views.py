from quakestats.web import app, data_store
import flask
from passlib.hash import pbkdf2_sha256


@app.template_global()
def user():
    return flask.g.user


@app.before_request
def attach_user():
    # completely rely on flask cookie signing capabilites
    try:
        flask.g.user = flask.session['username']
    except KeyError:
        flask.g.user = None


@app.route('/')
def index():
    return flask.render_template(
        'home.html', js_context={'view': 'HOME'})


@app.route('/match/<match_guid>')
def match(match_guid):
    return flask.render_template(
        'match.html', js_context={'view': 'MATCH', 'match_guid': match_guid})


@app.route('/player/<id>')
def player(id):
    return flask.render_template(
        'base.html', js_context={'view': 'Player', 'id': id})


@app.route('/maps')
def maps():
    return flask.render_template(
        'maps.html', js_context={'view': 'MAPS'})


@app.route('/login', methods=['POST'])
def login():
    try:
        username = flask.request.form['username']
        password = flask.request.form['password']
    except KeyError:
        pass
    else:
        if username and password:
            user = data_store().get_user(username)
            if user and pbkdf2_sha256.verify(password, user['password']):
                flask.session['username'] = username

    return flask.redirect('/')


@app.route('/logout')
def logout():
    if 'username' in flask.session:
        del flask.session['username']
    return flask.redirect('/')
