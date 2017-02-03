
def get_base_stats(finger, stats):
    num_cores = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])
    base_prefix = finger + '.base'

    base_stats = {
        base_prefix + '.count': 1,
        #base_prefix + '.load_1_min': last['cpu']['load_average'],
        #base_prefix + '.load_fractional': load_fractional(stats, host),
        base_prefix + '.cpu': get_cpu_percent(stats, num_cores),
        base_prefix + '.memory': get_memory_percent(stats),
        base_prefix + '.swap': get_swap_percent(stats),
        #base_prefix + '.net_upload': network_tx_kps(stats),
        #base_prefix + '.net_download': network_rx_kps(stats)
    }

    return base_stats


def get_network_stats(finger, stats):
    network_path = finger + '.base.network'

    def reduce_docker_interface(network_stats, docker_interface):
        interface_name, interface_stats = docker_interface
        interface_path = network_path + '.' + interface_name

        return add_interface_stats(network_path, interface_path, interface_stats.items(), network_stats)

    return reduce(reduce_docker_interface, stats['networks'].items(), {})


"""
BASE METRICS UTILS
"""


def get_cpu_percent(stats, num_cores):
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


def get_memory_percent(stats):
    memory_usage = stats['memory_stats']['usage']
    memory_limit = stats['memory_stats']['limit']

    return float(memory_usage) / float(memory_limit) * 100.0


def get_swap_percent(stats):
    swap_percent = 0.0

    swap_usage = stats['memory_stats']['stats']['swap']
    swap_total = stats['memory_stats']['stats']['total_swap']

    if swap_usage > 0 and swap_total > 0:
        swap_percent = float(swap_usage) / float(swap_total) * 100.0

    return swap_percent


"""
NETWORK METRICS UTILS
"""


# a dictionary mapping docker stats metrics to our own base metrics
docker_to_base_network_metrics = {
    'rx_bytes':     'bytes_recv',
    'rx_dropped':   'dropout',
    'rx_errors':    'errout',
    'rx_packets':   'packets_recv',
    'tx_bytes':     'bytes_sent',
    'tx_dropped':   'dropin',
    'tx_errors':    'errin',
    'tx_packets':   'packets_sent'
}


# add all the interface level metrics (ie: finger.networks.eth0.bytes_recv, etc.)
# as well as incremeting the top level metrics (ie: finger.networks.bytes_recv, etc.)
def add_interface_stats(network_path, interface_path, interface_stats, network_stats):

    def reduce_interface_stats(network_stats, interface_stat):
        key, value = interface_stat

        metric_name = docker_to_base_network_metrics[key]

        network_metric_path = network_path + '.' + metric_name
        network_stats[network_metric_path] = network_stats.get(network_metric_path, 0) + value

        interface_metric_path = interface_path + '.' + metric_name
        network_stats[interface_metric_path] = value

        return network_stats

    return reduce(reduce_interface_stats, interface_stats, network_stats)
