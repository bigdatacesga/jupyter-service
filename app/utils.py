import registry
import threading
import time
import requests
import socket
import hashlib
from . import app

ORCHESTRATOR_ENDPOINT = app.config.get('ORCHESTRATOR_ENDPOINT')


class ProcessPool(object):
    """A pool of processes"""
    def __init__(self):
        self._pool = {}

    def add(self, user, session, proc):
        if user not in self._pool:
            self._pool[user] = {}
        self._pool[user][session] = proc

    def remove(self, user, session):
        if user in self._pool and session in self._pool[user]:
            del self._pool[user][session]

    def get(self, user, session):
        if user in self._pool and session in self._pool[user]:
            return self._pool[user][session]
        else:
            return None

    def get_all(self):
        return self._pool

    def from_user(self, user):
        return self._pool[user]


def public_ip_address():
    """Returns the public IP address of the node"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    address = s.getsockname()[0]
    s.close()
    return address


def next_free_port():
    """Returns the next free port in the server"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 0))
    free_port = s.getsockname()[1]
    s.close()
    return free_port


def generate_id(body):
    """Generates a new jupyter session ID"""
    return hashlib.md5(body).hexdigest()


def validate(data, required_fields):
    """Validate if all required_fields are in the given data dictionary"""
    if all(field in data for field in required_fields):
        return True
    return False


def trim_dn(username, version, framework, dn):
    dn = dn.replace("instances", "")
    if username is not None:
        dn = dn.replace("/{}".format(username), "")
    if version is not None:
        dn = dn.replace("/{}".format(version), "")
    if framework is not None:
        dn = dn.replace("/{}".format(framework), "")
    return dn


def print_full_instance(instance):
    """ Try to get all the info from an instance or if error, return the dn"""
    try:
        return {
            "result": "success",
            "uri": str(instance.dn).replace("instances", "clusters"),
            "data": {
                "name": instance.dnsname,
                "dn": instance.dn,
                "status": instance.status
            }
        }
    except registry.KeyDoesNotExist as e:
        return {
            "result": "failure",
            "uri": str(instance.dn),
            "message": e.message
        }


def print_instance(instance, filters):
    """ Try to get the basic info from the instance or if error, return the dn"""
    (username, service, version) = filters
    try:
        return {
            "result": "success",
            # FIXME we have to return the full uri so that the interface
            # works, plus the "instances" part of the uri has to be
            # replaced by "clusters" so that it matches the endpoint
            "uri": str(instance.dn).replace("instances", "clusters"),
            "data": {
                "name" : instance.dnsname,
                "dn" : instance.dn,
                "status" : instance.status
            }
        }
    except registry.KeyDoesNotExist as e:
        return {
            "result": "failure",
            "uri": str(instance.dn),
            "message": e.message
        }


def launch_orchestrator_when_ready(clusterdn):
    """Launch the orchestrator process"""
    cluster = registry.get_cluster(dn=clusterdn)
    clusterid = registry.id_from(clusterdn)

    def orchestrate_when_cluster_is_ready():
        # TODO Use a blocking kv query to have inmediate notification
        app.logger.info('Waiting for cluster nodes to be scheduled')
        while cluster.status != 'scheduled':
            time.sleep(5)
        app.logger.info('All cluster nodes has been scheduled')
        # Wait so containers can boot
        #app.logger.info('Waiting 20s for containers to boot')
        #time.sleep(20)
        app.logger.info('Launching orchestrator')
        requests.post('{}/{}'.format(ORCHESTRATOR_ENDPOINT, clusterid))

    t = threading.Thread(target=orchestrate_when_cluster_is_ready)
    t.daemon = True
    t.start()
