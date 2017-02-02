
# commented metric path are the one that we can't get with basic docker stats api

def get_base_stats(finger, stats):
    num_cores = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])

    base_stats = {
        finger + '.base.count': 1,
        #finger + '.base.load_1_min': last['cpu']['load_average'],
        #finger + '.base.load_fractional': load_fractional(stats, host),
        finger + '.base.cpu': cpu_percent(stats, num_cores),
        finger + '.base.memory': memory_percent(stats),
        finger + '.base.swap': swap_percent(stats),
        #finger + '.base.net_upload': network_tx_kps(stats),
        #finger + '.base.net_download': network_rx_kps(stats)
    }

    return base_stats


"""
def get_network_stats(finger, stats):


def get_cpu_stats(finger, stats):


def get_memory_stats(finger, stats):


def get_diskio_stats(finger, stats):
"""


"""
BASE METRICS UTILS
"""


def cpu_percent(stats, num_cores):
    cpu_percent = 0.0
    num_cores = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])

    cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage']
    system_usage = stats['cpu_stats']['system_cpu_usage']

    prev_cpu_usage = stats['precpu_stats']['cpu_usage']['total_usage']
    prev_system_usage = stats['precpu_stats']['system_cpu_usage']

    # calculate the change for the cpu usage of the container in between readings
    cpu_delta = float(cpu_usage) - float(prev_cpu_usage)

    # calculate the change for the entire system between readings
    system_delta = float(system_usage) - float(prev_system_usage)

    if system_delta > 0.0 and cpu_delta > 0.0:
        cpu_percent = (cpu_delta / system_delta) * float(num_cores) * 100.0

    return cpu_percent


def memory_percent(stats):
    memory_usage = stats['memory_stats']['usage']
    memory_limit = stats['memory_stats']['limit']

    return float(memory_usage) / float(memory_limit) * 100.0


def swap_percent(stats):
    swap_percent = 0.0

    swap_usage = stats['memory_stats']['stats']['swap']
    swap_total = stats['memory_stats']['stats']['total_swap']

    if swap_usage > 0 and swap_total > 0:
        swap_percent = float(swap_usage) / float(swap_total) * 100.0

    return swap_percent


""" These are old methods that was used when we had cadvisor

def load_fractional(stats, host):
    return float(stats[-1]['cpu']['load_average']) / float(host['num_cores'])


def network_tx_kps(stats):
    n_prev_stats = min(10, len(stats))
    network_tx_now = stats[-1]['network']['tx_bytes']
    network_tx_prev = stats[-n_prev_stats]['network']['tx_bytes']

    return ((network_tx_now - network_tx_prev) / 1024) / n_prev_stats


def network_rx_kps(stats):
    n_prev_stats = min(10, len(stats))
    network_rx_now = stats[-1]['network']['rx_bytes']
    network_rx_prev = stats[-n_prev_stats]['network']['rx_bytes']
    return ((network_rx_now - network_rx_prev) / 1024) / n_prev_stats
"""
