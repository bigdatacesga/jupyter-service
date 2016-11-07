from flask import abort, jsonify, request, g, url_for
from . import api, app
from . import utils
import json
import requests
import registry
import kvstore
import subprocess
import time
from .decorators import restricted, asynchronous

CONSUL_ENDPOINT = app.config.get('CONSUL_ENDPOINT')
MESOS_FRAMEWORK_ENDPOINT = app.config.get('MESOS_FRAMEWORK_ENDPOINT')

registry.connect(CONSUL_ENDPOINT)
kv = kvstore.Client(CONSUL_ENDPOINT)

pool = utils.ProcessPool()

@api.route('/servers', methods=['POST'])
@restricted(role='ROLE_USER')
def start_server():
    """Start a new jupyter server"""
    address = utils.public_ip_address()
    port = utils.next_free_port()
    proc = start_jupyter(address, port)
    jupyter_url = 'http://{}:{}'.format(address, port)
    jupyter_id = utils.generate_id(g.user + jupyter_url + time.time())
    pool.add(g.user, jupyter_id, proc)
    kv.set('jupyter/{}/{}'.format(g.user, jupyter_id), jupyter_url)
    return '', 201, {'Location': jupyter_url}


@api.route('/servers/<username>/<session>', methods=['DELETE'])
@restricted(role='ROLE_USER')
def stop_server(username, session):
    """Stops the given server instance"""
    if username != g.user:
        return jsonify({'status': 401, 'error': 'unauthorized'}), 401
    proc = pool.get_process(username, session)
    if proc:
        proc.terminate()
        pool.remove(username, session)
    return jsonify({'sessions': proc.get(g.user)})


@api.route('/servers/<username>', methods=['GET'])
@restricted(role='ROLE_USER')
def list_active_servers():
    """Get the current list of active servers"""
    products = registry.query_products() or list()
    return jsonify({'products': list(set([p.name for p in products]))})

def start_jupyter(address, port):
    #cmd = '''PYSPARK_DRIVER_PYTHON=jupyter \
             #PYSPARK_DRIVER_PYTHON_OPTS="notebook --no-browser --ip={} --port={}" \
             #pyspark'''.format(address, port)

    cmd = ['sudo', '-l', g.user, '-c', 'scripts/start_jupyter_without_password']
    return subprocess.Popen(cmd, shell=True)
