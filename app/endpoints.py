from flask import jsonify, request, g, url_for
from . import api, app
from . import utils
import registry
import kvstore
import subprocess
import select
import time
from .decorators import restricted

CONSUL_ENDPOINT = app.config.get('CONSUL_ENDPOINT')
START_JUPYTER_SCRIPT = app.config.get('START_JUPYTER_SCRIPT')

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
    jupyter_id = utils.generate_id(g.user + jupyter_url + str(time.time()))
    pool.add(g.user, jupyter_id, proc)
    kv.set('jupyter/{}/{}'.format(g.user, jupyter_id), jupyter_url)
    return '', 201, {'Location': jupyter_url}


@api.route('/servers/<username>/<session>', methods=['DELETE'])
@restricted(role='ROLE_USER')
def stop_server(username, session):
    """Stops the given server instance"""
    if username != g.user:
        return jsonify({'status': 401, 'error': 'unauthorized'}), 401
    proc = pool.get(username, session)
    if proc:
        proc.terminate()
        pool.remove(username, session)
    return jsonify({'sessions': proc.get(g.user)})


@api.route('/servers/<username>', methods=['GET'])
@restricted(role='ROLE_USER')
def list_active_servers(username):
    """Get the current list of active servers"""
    if username != g.user:
        return jsonify({'status': 401, 'error': 'unauthorized'}), 401
    procs = pool.from_user(username)
    return jsonify({'sessions': procs})


@api.route('/servers/<username>/<session>', methods=['GET'])
@restricted(role='ROLE_USER')
def get_session_logs(username, session):
    """Returns the logs of the given session"""
    if username != g.user:
        return jsonify({'status': 401, 'error': 'unauthorized'}), 401
    proc = pool.get(username, session)
    stdout = ''
    stderr = ''
    if proc:
        stdout = read_pipe_output_nonblocking(proc.stdout)
        stderr = read_pipe_output_nonblocking(proc.stderr)
    return jsonify({'stdout': stdout, 'stderr': stderr})


def start_jupyter(address, port):
    #cmd = '''PYSPARK_DRIVER_PYTHON=jupyter \
             #PYSPARK_DRIVER_PYTHON_OPTS="notebook --no-browser --ip={} --port={}" \
             #pyspark'''.format(address, port)

    cmd = ['sudo', '-u', g.user, '-i', START_JUPYTER_SCRIPT, address, port]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)

def read_pipe_output_nonblocking(pipe, retVal=''):
    while (select.select([pipe], [], [], 1)[0] != []):
        retVal += pipe.read(1)
        return retVal
