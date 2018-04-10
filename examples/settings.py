# writable directory, all raw data will be stored there
# leave empty string to disable
RAW_DATA_DIR = '/tmp/quakestats/data'

# secret token used for minimalistic auth, e.g. post new results
ADMIN_TOKEN = 'mysecret'

# secret key used to encrypt cookies (see flask session docs)
SECRET_KEY = 'somesecret'

# name of database
# TODO add more DB config settings
MONGO_DBNAME = 'quakestats'

# server domain - kind of server group identification, required
# server domain has to be set, used to calculate name hashes, and match ids
# the idea is to support multiple server domains without id/name clash
# e.g. to have logs from 5 servers from domainA and 3 servers from domainB
# players with the same name won't clash between distinct domains
# Currently only single domain is supported however the machinery underneath
# is implemented, the only thing left to do is e.g to set domain dynamically
# in WEB API
SERVER_DOMAIN = 'mydomain'