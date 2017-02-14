import logging
import grequests
import sys
import getopt
import time
import dl_lib
import os
import re

logger = logging.getLogger('TAG')
os.environ['NO_PROXY'] = '127.0.0.1'

# will catch (numbers | uuid and hashed strings | garbage)
label_regex = '^(\d+)|([a-f0-9-]{32,})|(true|false|null|nil|none|undefined)|.*[\[\]\{\}].*$'
label_pattern = re.compile(label_regex)

def tag(ctx):
    logger.info("tagging")

    try:
        containers = dl_lib.get_containers()
        tag_containers(ctx, containers)
    except Exception as ex:
        logger.error("tagging failed: %s" % ex, exc_info=True)


def tag_containers(ctx, containers):
    api_host = ctx['api_host']
    headers = dl_lib.get_request_headers(ctx)

    def create_request(container):
        tags = get_tags(ctx, container)
        data = {'tags': ','.join(tags)}
        finger = dl_lib.get_container_hash(container)

        url = "%s/agents/%s/tags" % (api_host, finger)
        return grequests.put(url, json=data, headers=headers)

    reqs = map(create_request, containers)
    grequests.map(reqs)


def get_tags(ctx, container):
    tags = ["all", "docker"]
    tags += [container.attrs["Config"]["Image"]]
    tags += get_container_env_vars(container)
    tags += [dl_lib.get_container_real_host_name()]
    tags += get_container_labels(container)

    return [t.replace('/', ':') for t in set(filter(None, tags))]


def get_container_env_vars(container):
    container_env_vars = dl_lib.get_container_env_vars(container)
    return [container_env_vars[key] for key in container_env_vars if key in ['ENV', 'APP_NAME']]


def get_container_labels(container):
    def filter_labels(label):
        return not label_pattern.match(label.lower())

    labels = container.attrs['Config']['Labels'].values()
    return filter(filter_labels, labels)


def main(argv):
    ctx = {
        "tag_interval": 10,
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
        tag(ctx)
        time.sleep(ctx['tag_interval'])


def usage():
    usage = """tag.py
    -h --help                   Prints this
    -a --apikey <apikey>        Your dataloop api key
    -u --apiurl <apiurl>        The dataloop api url (default to "https://agent.dataloop.io")
    """
    print usage


if __name__ == "__main__":
    main(sys.argv[1:])
