import logging
import cgroups
import time

logger = logging.getLogger('DOCKERSTATS')

RATE_INTERVAL = 5


def get_metrics(rootfs, containers):
    metrics = {}
    mountpoints = cgroups.get_mountpoints(rootfs)

    _get_containers_stats(rootfs, mountpoints, containers, "prev_stats")
    time.sleep(RATE_INTERVAL)
    _get_containers_stats(rootfs, mountpoints, containers, "now_stats")

    for container in containers:
        container_metrics = _get_container_metrics(container)
        metrics.update(container_metrics)

    return metrics


def _get_containers_stats(rootfs, mountpoints, containers, key):
    for container in containers:
        stats = _get_container_stats(rootfs, mountpoints, container)
        setattr(container, key, stats)


def _get_container_stats(rootfs, mountpoints, container):
    container_cgroups = cgroups.find_container_cgroups(rootfs, mountpoints, container)
    stats = {
        "net":      cgroups.get_net_stats(rootfs, container),
        "blkio":    cgroups.get_blkio_stats(container_cgroups["blkio"]),
        "cpuacct":  cgroups.get_cpu_stats(rootfs, container_cgroups["cpuacct"]),
        "memory":   cgroups.get_memory_stats(rootfs, container_cgroups["memory"]),
    }

    return stats


def _get_container_metrics(container):
    base_path = container.finger + '.base'
    metrics = {
        base_path + '.count': 1
    }

    now_stats = container.now_stats
    prev_stats = container.prev_stats

    metrics.update(_get_disk_metrics(base_path, now_stats.get('blkio'), prev_stats.get('blkio')))
    metrics.update(_get_cpu_metrics(base_path, now_stats.get('cpuacct'), prev_stats.get('cpuacct')))
    metrics.update(_get_memory_metrics(base_path, now_stats.get('memory')))
    metrics.update(_get_network_metrics(base_path, now_stats.get('net'), prev_stats.get('net')))

    return metrics


"""
disk metrics
"""

def _get_disk_metrics(base_path, now_stats, prev_stats):
    disk_path = base_path + '.disk'
    metrics = {}

    for metric, value in now_stats.iteritems():
        path = disk_path + '.' + metric
        per_sec_path = path + '_per_sec'

        metrics[path] = value
        metrics[per_sec_path] = (float(value) - float(prev_stats.get(metric))) / RATE_INTERVAL

    return metrics


"""
cpu metrics
"""


def _get_cpu_metrics(base_path, now_stats, prev_stats):
    cpu_path = base_path + '.cpu'
    num_cores = now_stats.get('cores')

    system_percent, user_percent, usage_percent = 0.0, 0.0, 0.0
    total_delta = now_stats.get('total') - prev_stats.get('total')

    if total_delta > 0:
        total_delta_per_sec = float(total_delta) / RATE_INTERVAL

        usage_delta = now_stats.get('usage') - prev_stats.get('usage')
        if usage_delta > 0:
            usage_delta_per_sec = float(usage_delta) / RATE_INTERVAL
            usage_percent = usage_delta_per_sec / total_delta_per_sec * num_cores * 100

        system_delta = now_stats.get("system") - prev_stats.get('system')
        if system_delta > 0:
            system_delta_per_sec = float(system_delta) / RATE_INTERVAL
            system_percent = system_delta_per_sec / total_delta_per_sec * num_cores * 100

        user_delta = now_stats.get('user') - prev_stats.get('user')
        if user_delta > 0:
            user_delta_per_sec = float(user_delta) / RATE_INTERVAL
            user_percent = user_delta_per_sec / total_delta_per_sec * num_cores * 100

    metrics = {
        cpu_path + '.cores': num_cores,
        cpu_path + '.user': user_percent,
        cpu_path + '.system': system_percent,
        cpu_path: usage_percent,
    }

    return metrics


"""
memory metrics
"""

def _get_memory_metrics(base_path, stats):
    memory_path = base_path + '.memory'

    metrics = {}
    for metric, value in stats.iteritems():
        if metric in ["memory", "swap"]:
            path = base_path + '.' + metric
        else:
            path = memory_path + '.' + metric
        metrics[path] = value

    return metrics


"""
network metrics
"""

def _get_network_metrics(base_path, now_stats, prev_stats):
    network_path = base_path + '.network'
    metrics = {}

    for metric, value in now_stats.iteritems():
        path = network_path + '.' + metric
        per_sec_path = path + '_per_sec'

        metrics[path] = value
        metrics[per_sec_path] = (float(value) - float(prev_stats.get(metric))) / RATE_INTERVAL

        if metric == 'bytes_recv':
            metrics[base_path + '.net_download'] = metrics[per_sec_path] / 1024

        elif metric == 'bytes_sent':
            metrics[base_path + '.net_upload'] = metrics[per_sec_path] / 1024

    return metrics
