import logging
import sys

LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logger(ctx):
    if ctx['debug']:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    try:
        logging.basicConfig(format=LOG_FORMAT,
                            datefmt=LOG_DATE_FORMAT,
                            stream=sys.stdout,
                            level=log_level)

    except IOError:
        raise Exception("Error setting up logger")
