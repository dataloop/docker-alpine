import logging
import docker
import socket
import itertools
import uuid
import os
import re

logger = logging.getLogger("DOCKERUTIL")

UUID_HASH = uuid.UUID("12345678123456781234567812345678")

system_uuid_paths = [
    "/sys/class/dmi/id/product_uuid",
    "/proc/device-tree/system-id",
    "/proc/device-tree/vm,uuid",
    "/etc/machine-id",
]

# will catch (numbers | uuid and hashed strings | garbage | list and dict)
label_regex = "^(\d+)|([a-f0-9-]{32,})|(true|false|null|nil|none|undefined)|.*[\[\]\{\}].*$"
label_pattern = re.compile(label_regex)

is_k8s = "KUBERNETES_PORT" in os.environ

# connect to the docker server
docker_client = docker.from_env(
    assert_hostname=False,
    version="auto",
    timeout=5,
)


def list_containers():
    """Return a list of running containers."""
    containers = docker_client.containers.list()

    if is_k8s:
        return filter(_filter_kube_container, containers)

    return filter(_filter_host_container, containers)


def get_container_hashes(containers):
    return set(map(get_hash, containers))


def get_hash(container):
    """The container hash returned here is the dataloop agent finger id."""
    return _hash_id("/docker/" + container.id)


def get_image(container):
    return container.attrs.get("Config", {}).get("Image", "") or ""


def get_pid(container):
    return container.attrs.get("State", {}).get("Pid", "") or ""


def get_processes(container):
    """Get and group/count the processes running inside the container."""
    docker_processes = container.top().get("Processes", []) or []

    def extract_docker_processes(process):
        return process[len(process) - 1]

    processes = map(extract_docker_processes, docker_processes)

    def serialize(name, group):
        return "%s:%s" % (name, len(list(group)))

    processes_out = list(
        (serialize(k, v) for k, v in itertools.groupby(processes)))

    return processes_out


def get_ips(container):
    """Return a list of ip addresses of all the container networks."""
    container_networks = container.attrs.get("NetworkSettings", {}).get("Networks", {}) or {}

    def map_container_network(network):
        return network.get("IPAddress", None)

    return filter(None, map(map_container_network, container_networks.values()))


def get_env_variables(container):
    """If container env variables follow ENV=VALUE pattern, return them as a dict."""
    env_variables = {}

    for env_var in container.attrs["Config"]["Env"]:
        try:
            key, value = env_var.split("=", 1)
            env_variables[key] = value
        except:
            continue

    return env_variables


def get_labels(container):

    def filter_labels(label):
        return not label_pattern.match(label.lower())

    labels = container.attrs.get("Config", {}).get("Labels", {}) or {}
    return filter(filter_labels, labels.values())


def get_container_hostname(container):
    return container.id[:12]


def get_host_hostname():
    """Return the `Name` from `docker info`."""
    try:
        return docker_client.info().get("Name")
    except Exception as e:
        logger.warn("Unable to retrieve hostname using docker API, %s", str(e))
        return ""


def get_system_uuid():
    for uuid_path in system_uuid_paths:
        if not os.path.isfile(uuid_path):
            continue

        uuid_file = open(uuid_path)
        uuid = uuid_file.readline().strip()
        if uuid:
            return uuid


def _hash_id(id):
    return str(uuid.uuid5(UUID_HASH, id))


# exclude the dataloop-docker container
def _filter_host_container(container):
    return container.id[:12] != socket.gethostname()


# exclude "kube-system" and paused containers
def _filter_kube_container(container):
    config = container.attrs.get("Config", {}) or {}

    image = config.get("Image", "") or ""
    labels = config.get("Labels", {}) or {}

    is_kube_system = labels.get("io.kubernetes.pod.namespace", "") == "kube-system"
    is_paused = re.search("google_containers/pause", image)
    is_host = labels.get("io.kubernetes.pod.name", "") == socket.gethostname()

    return not is_kube_system and not is_paused and not is_host
