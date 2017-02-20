import time
import docker_stats_old


RATE_INTERVAL = 5


def get_metrics(containers):
    metrics = {}

    for c in containers:
        try:
            c.prev_stats = c.stats(stream=False)
        except Exception, e:
            c.prev_stats = None

    time.sleep(RATE_INTERVAL)

    for c in containers:
        try:
            c.now_stats = c.stats(stream=False)
        except Exception, e:
            c.now_stats = None

    for container in containers:
        if container.prev_stats and container.now_stats:
            container_metrics = get_container_metrics(container)
            metrics.update(container_metrics)

    return metrics


def get_container_metrics(container):
    base_metrics = {}

    finger = container.finger
    prev_stats = container.prev_stats
    now_stats  = container.now_stats

    base_metrics.update(get_base_metrics(finger, prev_stats, now_stats))
    # legacy, cadvisor type metrics
    base_metrics.update(docker_stats_old.get_metrics(finger, now_stats))

    return base_metrics


def get_base_metrics(finger, prev_stats, stats):
    base_path = finger + '.base'

    # missing: load_1_min and load_fractional
    base_stats = {
        base_path + '.count': 1,
        base_path + '.cpu': get_base_cpu_percent(stats),
        base_path + '.memory': get_memory_percent(stats['memory_stats']),
        base_path + '.swap': get_swap_percent(stats['memory_stats']),
    }

    base_stats.update(get_base_network_metrics(base_path, prev_stats['networks'], stats['networks']))

    return base_stats



"""
base cpu metrics
"""

def get_base_cpu_percent(stats):
    cpu_percent = 0
    num_cores = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])

    cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage']
    system_usage = stats['cpu_stats']['system_cpu_usage']

    prev_cpu_usage = stats['precpu_stats']['cpu_usage']['total_usage']
    prev_system_usage = stats['precpu_stats']['system_cpu_usage']

    # calculate the change for the cpu usage of the container in between readings
    cpu_delta = cpu_usage - prev_cpu_usage

    # calculate the change for the entire system between readings
    system_delta = system_usage - prev_system_usage

    if system_delta > 0 and cpu_delta > 0:
        cpu_percent = float(cpu_delta) / float(system_delta) * num_cores * 100

    return cpu_percent



"""
base memory metrics
"""


def get_memory_percent(memory_stats):
    memory_usage = memory_stats.get('usage', None)
    memory_limit = memory_stats.get('limit', None)

    if memory_usage is None or memory_limit is None:
        return None

    return float(memory_usage) / float(memory_limit) * 100


def get_swap_percent(memory_stats):
    swap_percent = 0
    stats = memory_stats.get('stats', {})

    swap_usage = stats.get('swap', None)
    swap_total = stats.get('total_swap', None)

    if swap_usage is None or swap_total is None:
        return None

    if swap_usage > 0 and swap_total > 0:
        swap_percent = float(swap_usage) / float(swap_total) * 100.0

    return swap_percent



"""
base network metrics
"""


def get_base_network_metrics(base_path, prev_stats, stats):
    prev_network_stats = calculate_base_network_stats(prev_stats)
    network_stats = calculate_base_network_stats(stats)

    net_upload = (network_stats['tx_bytes'] - prev_network_stats['tx_bytes']) / 1024 / RATE_INTERVAL
    net_download = (network_stats['rx_bytes'] - prev_network_stats['rx_bytes']) / 1024 / RATE_INTERVAL

    network_metrics = {
        base_path + '.net_upload': net_upload,
        base_path + '.net_download': net_download,
    }

    return network_metrics


def calculate_base_network_stats(network_stats):
    base_network_stats = {'rx_bytes': 0, 'tx_bytes': 0}

    for key, value in network_stats.items():
        base_network_stats['rx_bytes'] +=  value['rx_bytes']
        base_network_stats['tx_bytes'] +=  value['tx_bytes']

    return base_network_stats
