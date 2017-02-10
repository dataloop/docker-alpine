import logging
import os
import uuid
import docker
import sys
import grequests
import requests
import re
import unicodedata
import socket
from docker.client import DockerClient

os.environ['NO_PROXY'] = '127.0.0.1'
UUID_HASH = uuid.UUID('12345678123456781234567812345678')

system_uuid_paths = [
    "/sys/class/dmi/id/product_uuid",
    "/proc/device-tree/system-id",
    "/proc/device-tree/vm,uuid",
    "/etc/machine-id",
]

# logging config for all the py scripts that use dl_lib
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    stream=sys.stdout,
                    level=logging.WARN)

# connect to the docker server
if os.path.exists('/rootfs/var/run/docker.sock'):
    docker_cli = DockerClient(base_url='unix://rootfs/var/run/docker.sock', version='auto')
else:
    docker_cli = docker.from_env(assert_hostname=False)


"""
DOCKER UTILS
"""

def get_containers():
    containers = docker_cli.containers.list()

    def filter_host_container(container):
        if container.id[:12] != socket.gethostname():
            return container
        else:
            logger.debug("This container: %s" % container.id)

    return filter(filter_host_container, containers)


# try to ensure agent fingerprint backward compatibility
def get_container_hash(container):
    return hash_id("/docker/" + container.id)


def get_container_hashes(containers):
    return set(map(get_container_hash, containers))


def get_container_processes(container):
    process_list = []
    processes = container.top()["Processes"]

    for process in processes or []:
        process_list.append(process[len(process) -1] + ':1')

    return process_list


def get_container_network(container):
    ips = container.attrs["NetworkSettings"]["IPAddress"]
    interface = [
        {
            'interface': 'eth0',
            'addresses': [
                {
                    'ips': [ips],
                    'family': 'AF_INET'
                }
            ]
        },
        {
            'interface': 'lo0',
            'addresses': [
                {
                    'ips': [
                        '127.0.0.1'
                    ],
                    'family': 'AF_INET'
                }
            ]
        }
    ]
    return interface


def get_container_env_vars(container):
    env_tags = {}

    for env_var in container.attrs["Config"]["Env"]:
        try:
            key, value = env_var.split('=', 1)
            env_tags[key] = value
        except:
            continue

    return env_tags


def get_container_real_host_name():
    try:
        with open('/rootfs/etc/hostname', 'r') as f:
            hostname = f.read()
        return hostname.strip()
    except:
        return ""


"""
DATALOOP API UTILS
"""

def get_request_headers(ctx):
    return {
        "Content-type": "application/json",
        "Authorization": "Bearer " + ctx['api_key']
    }


def get_agents(ctx):
    system_uuid = get_system_uuid()
    agent_api = "%s/agents?mac=%s" % (ctx['api_host'], system_uuid)

    try:
        resp = requests.get(agent_api, headers=get_request_headers(ctx), timeout=5)
        resp.raise_for_status()
        return resp.json()
    except:
        logger.info("Failed to return agents by mac")


def get_agents_ids(agents):
    def get_agent_id(agent):
        return agent['id']

    return set(map(get_agent_id, agents))


def deregister_agents(ctx, agent_ids):
    api_host = ctx['api_host']
    headers = get_request_headers(ctx)

    def create_request(id):
        url = "%s/agents/%s/deregister" % (api_host, id)
        return grequests.post(url, headers=headers)

    reqs = map(create_request, agent_ids)
    grequests.map(reqs)


"""
MISC UTILS
"""

def hash_id(id):
    return str(uuid.uuid5(UUID_HASH, id))

def get_system_uuid():
    for uuid_path in system_uuid_paths:
        if not os.path.isfile(uuid_path):
            continue

        uuid_file = open(uuid_path)
        uuid = uuid_file.readline().strip()
        if uuid:
            return uuid

    raise OSError("Cannot read system_uuid")
