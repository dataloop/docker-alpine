import getopt
import sys
import os

from utils import api, docker_util

os.environ['NO_PROXY'] = '127.0.0.1'


def deregister_all(ctx):
    '''used as a cleanup task when dataloop-docker container is stopped'''

    containers = docker_util.list_containers()
    container_hashes = docker_util.get_container_hashes(containers)
    api.deregister_agents(ctx, container_hashes)


def main(argv):
    ctx = {
        "api_host": "https://agent.dataloop.io",
        "api_key": None,
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

    deregister_all(ctx)


def usage():
    usage = """deregister.py
    -h --help                   Prints this
    -a --apikey <apikey>        Your dataloop api key
    -u --apiurl <apiurl>        The dataloop api url (default to "https://agent.dataloop.io")
    """
    print usage


if __name__ == "__main__":
    main(sys.argv[1:])
