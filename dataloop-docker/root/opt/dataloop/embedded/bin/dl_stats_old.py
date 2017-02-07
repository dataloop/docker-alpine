
###############################
# DEPRECATED CADVISOR METRICS #
###############################


# missing: diskio
def get_metrics(finger, stats):
    metrics = {}

    metrics.update(get_network_metrics(finger, stats['networks']))
    metrics.update(get_cpu_metrics(finger, stats['cpu_stats']))
    metrics.update(get_memory_metrics(finger, stats['memory_stats']))
    metrics.update(get_diskio_metrics(finger, stats['blkio_stats']))

    return metrics



"""
network metrics
"""


def get_network_metrics(finger, stats):
    network_path = finger + '.network'

    def reduce_network_interface(network_metrics, network_interface):
        interface_name, interface_stats = network_interface
        interface_path = network_path + '.' + interface_name

        return add_interface_metrics(network_path, interface_path, interface_stats.items(), network_metrics)

    return reduce(reduce_network_interface, stats.items(), {})


def add_interface_metrics(network_path, interface_path, interface_stats, network_metrics):

    def reduce_interface_stats(network_metrics, interface_stat):
        key, value = interface_stat

        network_metric_path = network_path + '.' + key
        network_metrics[network_metric_path] = network_metrics.get(network_metric_path, 0) + value

        interface_metric_path = interface_path + '.' + key
        network_metrics[interface_metric_path] = value

        return network_metrics

    return reduce(reduce_interface_stats, interface_stats, network_metrics)



"""
cpu metrics
"""


def get_cpu_metrics(finger, stats):
    cpu_path = finger + '.cpu'
    cpu_metrics = {}

    cpu_metrics.update(get_throttling_metrics(cpu_path, stats.get('throttling_data', {})))
    cpu_metrics.update(get_usage_metrics(cpu_path, stats))

    return cpu_metrics


def get_throttling_metrics(cpu_path, throttling_stats):
    throttling_path = cpu_path + '.cfs'

    def reduce_throttling_stats(throttling_metrics, throttling_metric):
        key, value = throttling_metric

        metric_path = throttling_path + '.' + key
        throttling_metrics[metric_path] = value

        return throttling_metrics

    return reduce(reduce_throttling_stats, throttling_stats.items(), {})


def get_usage_metrics(cpu_path, cpu_stats):
    usage_path = cpu_path + '.usage'
    usage_stats = cpu_stats['cpu_usage']

    usage_metrics = {
        usage_path + '.system': cpu_stats.get('system_cpu_usage', None),
        usage_path + '.user': usage_stats['usage_in_usermode'],
        usage_path + '.total': usage_stats['total_usage'],
    }

    percpu_usage = usage_stats.get('percpu_usage', None)
    if percpu_usage:
        for index, value in enumerate(percpu_usage):
            percpu_path = usage_path + '.' + str(index)
            usage_metrics[percpu_path] = value

    return usage_metrics



"""
memory metrics
"""


def get_memory_metrics(finger, memory_stats):
    memory_path = finger + '.memory'

    memory_metrics = {
        memory_path + '.failcnt': memory_stats.get('failcnt', None),
        memory_path + '.usage': memory_stats.get('usage', None),
    }

    stats = memory_stats.get('stats', {})
    memory_stats_metrics = {
        memory_path + '.cache': stats.get('cache', None),
        memory_path + '.rss': stats.get('rss', None),
        memory_path + '.swap': stats.get('swap', None),
        memory_path + '.container_data.pgfault': stats.get('pgfault', None),
        memory_path + '.container_data.pgmajfault': stats.get('pgmajfault', None),
        memory_path + '.hierarchical_data.pgfault': stats.get('total_pgfault', None),
        memory_path + '.hierarchical_data.pgmajfault': stats.get('total_pgmajfault', None),
    }
    memory_metrics.update(memory_stats_metrics)

    return memory_metrics



"""
diskio metrics
"""

def get_diskio_metrics(finger, diskio_stats):
    diskio_path = finger + '.diskio'
    diskio_metrics = {}

    io_serviced_path = diskio_path + '.io_serviced.0.stats'
    io_serviced_stats = diskio_stats['io_serviced_recursive']

    for key, value in enumerate(io_serviced_stats):
        path = io_serviced_path + '.' + value['op']
        diskio_metrics[path] = value['value']

    io_service_bytes_path = diskio_path + 'io_service_bytes.0.stats'
    io_service_bytes_stats = diskio_stats['io_service_bytes_recursive']

    for key, value in enumerate(io_service_bytes_stats):
        path = io_service_bytes_path + '.' + value['op']
        diskio_metrics[path] = value['value']

    return diskio_metrics
