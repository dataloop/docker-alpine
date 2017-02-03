import logging
import socket
import sys
import getopt
import time
import dl_lib
import dl_stats

logger = logging.getLogger('METRICS')


def send_metrics(ctx):
    logger.info("metrics")

    try:
        containers = dl_lib.get_containers()
        metrics = get_metrics(containers)
        publish_metrics(ctx, metrics)
    except Exception as ex:
        logger.error("metrics failed: %s" % ex, exc_info=True)


def get_metrics(containers):
    metrics = {}
    for container in containers:
        container_metrics = get_container_metrics(container)
        metrics.update(container_metrics)

    return metrics


def get_container_metrics(container):
    finger = dl_lib.get_container_hash(container)
    stats = container.stats(stream=False)

    metrics = {}

    metrics.update(dl_stats.get_base_stats(finger, stats))
    metrics.update(dl_stats.get_network_stats(finger, stats))
    #metrics.update(dl_stats.get_cpu_stats(finger, stats))
    #metrics.update(dl_stats.get_memory_stats(finger, stats))
    #metrics.update(dl_stats.get_diskio_stats(finger, stats))

    return metrics


def publish_metrics(ctx, metrics):
    sock = socket.socket()
    sock.connect((ctx["graphite_host"], ctx["graphite_port"]))

    for path, value in metrics.iteritems():
        if isinstance(value, int) or isinstance(value, float):
            message = "%s %s\n" % (path, value)
            sock.sendall(message)

    sock.close()


def main(argv):
    ctx = {
        "metric_interval": 30,
        "api_host": "https://agent.dataloop.io",
        "graphite_host": "graphite.dataloop.io",
        "graphite_port": 2003,
        "api_key": None
    }

    try:
        opts, args = getopt.getopt(argv, "ha:u:s:p:", ["help", "apikey=", "apiurl=", "graphiteserver=", "graphiteport="])

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
        elif opt in ("-s", "--graphiteserver"):
            ctx['graphite_host'] = arg
        elif opt in ("-p", "--graphiteport"):
            ctx['graphite_port'] = int(arg)

    if ctx['api_key'] is None:
        usage()
        sys.exit(2)

    while True:
        send_metrics(ctx)
        time.sleep(ctx['metric_interval'])


def usage():
    usage = """metrics.py
    -h --help                               Prints this
    -a --apikey <apikey>                    Your dataloop api key
    -u --apiurl <apiurl>                    The dataloop api url (default to "https://agent.dataloop.io")
    -s --graphiteserver <graphiteserver>    The graphite url (default to "graphite.dataloop.io")
    -p --graphiteport <graphiteport>        The graphite port (default to "2003")
    """
    print usage


if __name__ == "__main__":
    main(sys.argv[1:])
