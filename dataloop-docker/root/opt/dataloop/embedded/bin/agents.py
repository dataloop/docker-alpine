import getopt
import logging
import sys
import time
import os
import requests

from utils import api, docker_util, logger_util

logger = logging.getLogger('AGENTS')

os.environ['NO_PROXY'] = '127.0.0.1'

loopback_interface = {
    'interface': 'lo0',
    'addresses': [{'ips': ['127.0.0.1'],'family': 'AF_INET'}]
}


def sync(ctx):
    logger.info("agents sync")

    try:
        containers = docker_util.list_containers()
        ctx['system_uuid'] = docker_util.get_system_uuid(ctx)
        ctx['host_finger'] = get_host_finger()

        ping_containers(ctx, containers)
        tag_containers(ctx, containers)
        deregister_dead_containers(ctx, containers)

    except Exception as ex:
        logger.error("agent sync failed: %s" % ex, exc_info=True)


def get_host_finger():
    finger = requests.get("http://localhost:8000").text
    # this endpoint returns the fingerprint with a newline, so strip whitespace
    return finger.strip()


def ping_containers(ctx, containers):

    def create_agent(container):
        return {
            'finger': docker_util.get_hash(container),
            'name': container.name,
            'mac': ctx['system_uuid'],
            'hostname': docker_util.get_container_hostname(container),
            'os_name': 'docker',
            'os_version': '',
            'processes': docker_util.get_processes(container),
            'interfaces': _get_agent_interface(container),
            'mode': 'DEFAULT',
            'interpreter': '/usr/bin/python',
            'container_id': container.id,
            'parent': ctx['host_finger']
        }

    agents = map(create_agent, containers)
    api.ping_agents(ctx, agents)


def tag_containers(ctx, containers):

    def create_tags(container):
        return {
            'finger': docker_util.get_hash(container),
            'tags': _get_agent_tags(ctx, container)
        }

    agents = map(create_tags, containers)
    api.tag_agents(ctx, agents)


def deregister_dead_containers(ctx, containers):
    agents = api.list_agents(ctx, ctx['system_uuid'])
    agent_ids = set(map(lambda a: a['id'], agents))

    container_hashes = docker_util.get_container_hashes(containers)
    dead_containers = agent_ids - container_hashes
    api.deregister_agents(ctx, dead_containers)


def _get_agent_interface(container):
    ips = docker_util.get_ips(container)
    interfaces = [loopback_interface]

    if ips:
        ethernet_interface = {
            'interface': 'eth0',
            'addresses': [{'ips': ips, 'family': 'AF_INET'}]
        }
        interfaces.append(ethernet_interface)

    return interfaces


def _get_agent_tags(ctx, container):
    tags = ["all", "docker"]

    tags.append("container:%s" % docker_util.get_container_hostname(container))
    tags.append("parent:%s" % ctx['host_finger'])
    tags.append(docker_util.get_image(container))
    tags.append(docker_util.get_host_hostname())
    tags.append(docker_util.get_container_hostname(container))
    tags += _get_agent_env_vars(container)
    tags += docker_util.get_labels(container)

    sanitized = [t.replace('/', ':') for t in set(filter(None, tags))]
    return ','.join(sanitized)


def _get_agent_env_vars(container):
    container_env_vars = docker_util.get_env_variables(container)
    return [container_env_vars[key] for key in container_env_vars if key in ['ENV', 'APP_NAME']]


def main(argv):
    ctx = {
        "sync_interval": 10,
        "api_host": "https://agent.dataloop.io",
        "api_key": None,
        "debug": False,
    }

    try:
        opts, args = getopt.getopt(argv, "ha:u:d", ["help", "apikey=", "apiurl=", "debug"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(2)
        elif opt in ("-a", "--apikey"):
            ctx['api_key'] = arg
        elif opt in ("-u", "--apiurl"):
            ctx['api_host'] = arg
        elif opt in ("-d", "--debug"):
            ctx["debug"] = True

    if ctx['api_key'] is None:
        usage()
        sys.exit(2)

    logger_util.setup_logger(ctx)

    while True:
        sync(ctx)
        time.sleep(ctx['sync_interval'])


def usage():
    usage = """agents.py
    -h --help                   Prints this
    -a --apikey <apikey>        Your dataloop api key
    -u --apiurl <apiurl>        The dataloop api url (default to "https://agent.dataloop.io")
    -d --debug                  Change log level to DEBUG, default to INFO
    """
    print usage


if __name__ == "__main__":
    main(sys.argv[1:])
