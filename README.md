# Quake Stats
[![Build Status](https://travis-ci.org/brabiega/quakestats.svg?branch=master)](https://travis-ci.org/brabiega/quakestats)
[![PyPI](https://img.shields.io/pypi/v/quakestats)](https://pypi.org/project/quakestats/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/quakestats)](https://pypi.org/project/quakestats/#files)

Quake 3 logs / Quake Live events processing project.

Allows to retrieve, process, analyze, store and present Quake matches.

The project doesn't aim to give global stats like [qlstats](http://qlstats.net) it's rather meant to store statistics from some server group (server domain). The origins of Quake Stats come from a group of players who occasionally play together and want to keep track of their matches... and to have fun from some custom made medals (badges) :)

## Overview
### Supported features:
* processing Quake 3 logs (log parsing, at the moment OSP mod only)
* processing Quake Live event streams (zmq listen, needs some work)
* translating (to some extent) Quake 3 logs into Quake Live events
* analysing matches
* storing matches in Database backend (Mongo DB)
* presenting match results through a web application

### Supported mods and game modes
Unfortunately only OSP FFA from Quake 3 is well tested as it was the main use case
#### mods
- [x] - OSP (http://www.orangesmoothie.org/tourneyQ3A/index.html)
- [x] - Quake Live - most of event processing is implemented
- [x] - Edawn
- [ ] - vanilla Q3 not supported due to missing ServerTime info
- [ ] - CPMA not supported due to missing ServerTime info

#### modes
- [x] - DUEL
- [x] - FFA
- [ ] - CA - partially implemented
- [ ] - TDM
- [ ] - CTF

### Custom medals
Are described here [resources.js](quakestats/static/js/resources.js)

### Examples
The stats are presented with fancy charts, custom medals, etc. See the examples below.
#### Total badges/medals board
![home1](examples/home1.png)
#### Total kills & deaths
![home2](examples/home2.png)
#### Single match Kill Death Ratio, Worst Enemy, Score over Time chart
![match1](examples/match1.png)

### Requirements
- Python 3.6+
- Instance of Mongo DB (pointed by ```settings.py```)
- Modern web browser (requires css grid-layout)

## How to setup
In order to setup the application you need to have python 3 (virtualenv recommended) and an instance of mongo DB.

### Installation
#### Install from pip package
```bash
pip install quakestats
```

#### Install from source code
Is also needed install ```quakestats``` package (in virtualenv if you are using it). To do that you could install it directly
```bash
pip install -r requirements.txt
python setup.py install
```

### Configuration file
The application is configured by setting ```QUAKESTATS_SETTINGS``` environment variable to path to configuration file.
See example [settings.py](examples/settings.py)

### Verify if everything is properly set up
Quake Stats provide a simple CLI with a command to verify an environment
```bash
quakestats status
```

Example output:
```
(venv) [user@pc quakestats]$ quakestats status
app -> version: 0.9.61
settings -> env var: /opt/quakestats/settings.py
settings -> RAW_DATA_DIR: /opt/quakestats/data
db -> ping: {'ok': 1.0}
webapp -> loadable: Quakestats webapp is loadable
```

### Run Quake Stats web app
You can setup Quake Stats web app with any websever you want (as long as it supports python, e.g. mod wsgi, uwsgi).
This documentation covers only running in *twisted* webserver

#### Run in twistd (example)
You can launch Quake Stats web application using ```twistd``` webserver. Just make sure to install twisted framework first.
Also make sure to use some recent version of twisted (tested with 18.7.0 installed by pip).
```bash
FLASK_APP="quakestats.web"; QUAKESTATS_SETTINGS=`pwd`/settings.py; twistd web --wsgi quakestats.web.app
```

## User/Admin guide
### Setup admin user
Admin user is used by web application to access some additional administrative operations. For now it's only setting map sizes. Just to have a list of recently used maps and their sizes. Nothing more at the moment.
```bash
# you need to run the command in proper python environment
# use "quakestats status" to check your environment
quakestats set-admin-pwd <yourpassword>
```

### Listening for Quake Live stats
Quake Live exposes server events through tcp socket authenticated with password.
Use following CLI command to listen and process such events.
```bash
quakestats collect-ql <ip> <port> <stats-password>
```

### Uploading Quake 3 log file
In order to process some data you need to send your match log file to web api endpoint ```/api/v2/upload```. By default mod ```osp``` is assumed.
Mod specific endpoint is served under ```/api/v2/upload/<mod>```, e.g. ```/api/v2/upload/edawn```
You need an ```ADMIN_TOKEN``` set in configuration.
```bash
curl -X POST --form file=@/path/to/your/games.log --form token=adminsecrettoken host:port/api/v2/upload
```
All log files with extracted matches are stored in directory determined by ```RAW_DATA_DIR``` config entry

### Using automated scrupt to send logs
Quakestats includes a script which is able to watch q3 log file and
automatically send match results when match end is detected.
You need to install quakestats (use python pip) package on the server where your log file is.
 Example usage:

```bash
# q3-log-watch --q3logfile ~/.q3a/osp/games.log --api-endpoint http://<QUAKESTATS URL> --api-token <ADMIN TOKEN>
q3-log-watch --q3logfile ~/.q3a/osp/games.log --api-endpoint http://localhost:8000 --api-token mytoken123
```

### Rebuilding database
You can rebuild your database using files stored in ```RAW_DATA_DIR``` with simple web api call or CLI.
```bash
curl -X POST host:port/api/v2/admin/rebuild --form token=adminsecrettoken
```
```bash
# you need to run the command in proper python environment
# use "quakestats status" to check your environment
quakestats rebuild-db
```
If you implement some new Medals or any other backend related feature this API call will clear previous data stored in DB and process all matches from data directory once again.

### Merging player results
Unfortunately the only way to distinguish players in Quake 3 servers is to use player nickname. When player changes his nickname between matches he will be treated as new unique player. In such cases admin can merge results of two specific players. Use with caution as it will rewrite history of all matches stored in database.
```bash
curl -X POST host:port/api/v2/admin/players/merge --form token=admintoken --form source_player_id=297f6272f79d4918c4efe098 --form target_player_id=df55e5cd4582d6f14cd20746
```
It will merge all results from player with id ```297f6272f79d4918c4efe098``` into player with id ```df55e5cd4582d6f14cd20746```. To find out how player ID is build see the development section.

### Importing preprocessed match log
Preprocessed match logs stored in ```RAW_DATA_DIR``` can be imported using admin match import API.
This can be particularly useful when e.g. debugging some bugs on dev infra.
```bash
curl -X POST --form file=@bugmatch.log --form token=admintoken host:port/api/v2/admin/match/import
```

## Development
### Tech stack
Python, Flask, MongoDB, d3.js, riot.js, zmq

### Building blocks
There are several 'responsibility bound' components

#### Dataprovider
Groups logic related to gathering data (logs, events), processing and analysis.

##### How does it work with Quake 3 Players
Quake 3 players don't have unique ID's so it's hard to distinguish players between matches. In order to overcome this problem each player has ```player_id``` assigned during match analysis. The ID is constructed as hash of ```SERVER_DOMAIN``` and player nickname as a result it's consistent between matches as long as player keeps his nickname and there is no nickname clash. Perhaps there is some better way? Server side auth?

#### Datasource
Groups logic related to storage backend and storage related operations

#### Web
Web application related components
- api - web API used by frontend and to retrieve Quake 3 logs
- views - typical flask views


#### Data flow
```
# Data gathering
Quake Live Data	(events) -> QLMatchFeeder >-------|
                                                  |----> Data Preprocessor (FullMatchReport)
Quake 3 Data (log) -> Q3MatchFeeder -> Q3toQL >---|

# Data procesing
Data Preprocessor (FullMatchReport) -> Data Analyzer (AnalysisResult)

# Data storage
Data Analyzer (AnalysisResult) -> StorageApi -> StorageBackend
```

#### Web data flow
```
Stats webapp ----| -> Web API -> StorageApi -> StorageBackend
```
### Extending
#### How to add new medal
- see [SpecialScores class](quakestats/dataprovider/analyzer/specials.py) - for special scores
- see [Badger class](quakestats/dataprovider/analyzer/badges.py) - for badges calculation
- see [JS resources](quakestats/static/js/resources.js) - to add new medal image

#### Running tests
```bash
make test
```
### Assets
Medals, icons, etc.
Some of the assets are missing it would be nice to find some free ones or draw them ;)

### TODO
- [ ] Add support for listening to Quake Live event publisher, minor work needed

### How to release new version
```bash
bumpversion <major|minor|patch> --commit --tag
```
