import getopt
import logging
import sys
import time
import grequests
import dl_lib
import os

logger = logging.getLogger('DISCOVER')
os.environ['NO_PROXY'] = '127.0.0.1'


def registration(ctx):
    logger.info("register sync")

    try:
        register_sync(ctx)
    except Exception as ex:
        logger.error("register sync failed: %s" % ex, exc_info=True)


def register_sync(ctx):
        agents = dl_lib.get_agents(ctx)
        agent_ids = dl_lib.get_agents_ids(agents)

        containers = dl_lib.get_containers()
        container_hashes = dl_lib.get_container_hashes(containers)

        logger.debug("agent_ids=%s container_hashes=%s", agent_ids, container_hashes)
        dead_containers = agent_ids - container_hashes
        destroy_agents(ctx, dead_containers)


def destroy_agents(ctx, agent_ids):
    api_host = ctx['api_host']
    headers = dl_lib.get_request_headers(ctx)

    def create_request(id):
        url = "%s/agents/%s/deregister" % (api_host, id)
        return grequests.post(url, headers=headers)

    reqs = map(create_request, agent_ids)
    grequests.map(reqs)


def main(argv):
    ctx = {
        "register_interval": 30,
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
        registration(ctx)
        time.sleep(ctx['register_interval'])


def usage():
    usage = """discover.py
    -h --help                   Prints this
    -a --apikey <apikey>        Your dataloop api key
    -u --apiurl <apiurl>        The dataloop api url (default to "https://agent.dataloop.io")
    """
    print usage


if __name__ == "__main__":
    main(sys.argv[1:])
