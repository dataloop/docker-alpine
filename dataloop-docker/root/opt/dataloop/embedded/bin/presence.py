import getopt
import logging
import socket
import sys
import time
import grequests
import dl_lib
import os

logger = logging.getLogger('PRESENCE')
os.environ['NO_PROXY'] = '127.0.0.1'


def ping(ctx):
    logger.info("pinging")

    try:
        containers = dl_lib.get_containers()
        for container in containers:
            logger.debug("found container: id=%s name=%s" % (container.id, container.name))

        ping_containers(ctx, containers)

    except Exception as ex:
        logger.error("ping failed: %s" % ex, exc_info=True)


def exception_handler(request, exception):
    logger.info(request.url, "| request failed")


def ping_containers(ctx, containers):
    api_host = ctx['api_host']
    headers = dl_lib.get_request_headers(ctx)

    system_uuid = dl_lib.get_system_uuid()
    host_name = str(socket.gethostname())

    def create_request(container):
        finger = dl_lib.get_container_hash(container)
        processes = dl_lib.get_container_processes(container)
        interfaces = dl_lib.get_container_network(container)

        details = {
            'name': container.name,
            'mac': system_uuid,
            'hostname': host_name,
            'os_name': 'docker',
            'os_version': '',
            'processes': processes,
            'container': '001',
            'interfaces': interfaces,
            'mode': 'SOLO'
        }

        url = "%s/agents/%s/ping" % (api_host, finger)
        return grequests.post(url, json=details, headers=headers, timeout=2)

    reqs = map(create_request, containers)
    grequests.map(reqs, exception_handler=exception_handler)


def main(argv):
    ctx = {
        "ping_interval": 10,
        "api_host": "https://agent.dataloop.io",
        "api_key": None
    }

    try:
        opts, args = getopt.getopt(argv, "ha:u:", ["help", "apikey=", "apiurl="])
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

    if ctx['api_key'] is None:
        usage()
        sys.exit(2)

    while True:
        ping(ctx)
        time.sleep(ctx['ping_interval'])


def usage():
    usage = """presence.py
    -h --help                   Prints this
    -a --apikey <apikey>        Your dataloop api key
    -u --apiurl <apiurl>        The dataloop api url (default to "https://agent.dataloop.io")
    """
    print usage


if __name__ == "__main__":
    main(sys.argv[1:])
