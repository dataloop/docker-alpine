import logging
import socket
import sys
import getopt
from utils import docker_util, docker_stats, logger_util

logger = logging.getLogger('METRICS')


def send_metrics(ctx):
    logger.info("metrics")

    try:
        containers = map(format_container, docker_util.list_containers())
        metrics = docker_stats.get_metrics(ctx["rootfs"], ctx["metric_interval"], containers)
        publish_metrics(ctx, metrics)

    except Exception as ex:
        logger.error("metrics failed: %s" % ex, exc_info=True)


def format_container(container):
    return {
        "finger": docker_util.get_hash(container),
        "pid": docker_util.get_pid(container)
    }


def publish_metrics(ctx, metrics):
    message = ""

    for path, value in metrics.iteritems():
        if isinstance(value, int) or isinstance(value, float):
            message += "%s %s\n" % (path, value)

    if message:
        sock = socket.socket()
        sock.connect((ctx["graphite_host"], ctx["graphite_port"]))
        sock.sendall(message)
        sock.close()


def main(argv):
    ctx = {
        "rootfs": "/rootfs",
        "metric_interval": 30,
        "graphite_host": "graphite.dataloop.io",
        "graphite_port": 2003,
        "debug": False,
    }

    try:
        opts, args = getopt.getopt(argv, "hs:p:r:d", ["help", "graphiteserver=", "graphiteport=", "rootfs=", "debug"])

    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(2)
        elif opt in ("-s", "--graphiteserver"):
            ctx['graphite_host'] = arg
        elif opt in ("-p", "--graphiteport"):
            ctx['graphite_port'] = int(arg)
        elif opt in ("-r", "--rootfs"):
            ctx['rootfs'] = arg
        elif opt in ("-d", "--debug"):
            ctx["debug"] = True

    logger_util.setup_logger(ctx)

    while True:
        send_metrics(ctx)


def usage():
    usage = """metrics.py
    -h --help                               Prints this
    -s --graphiteserver <graphiteserver>    The graphite url (default to "graphite.dataloop.io")
    -p --graphiteport <graphiteport>        The graphite port (default to "2003")
    -d --debug                  Change log level to DEBUG, default to INFO
    """
    print usage


if __name__ == "__main__":
    main(sys.argv[1:])
