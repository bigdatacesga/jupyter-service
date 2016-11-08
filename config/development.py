
# Secret passphrase
# FIXME: Temporarily SECRET must have the same value as SECRET_KEYS
#        due to the current spring boot implementation
SECRET = '/etc/keyczar/keys'
# Secret keyczar keys
SECRET_KEYS = '/etc/keyczar/keys'
# Fill as needed
DEBUG = True
IGNORE_AUTH = True
CONSUL_ENDPOINT = 'http://consul:8500/v1/kv'
START_JUPYTER_SCRIPT = 'scripts/start_jupyter_without_password'
