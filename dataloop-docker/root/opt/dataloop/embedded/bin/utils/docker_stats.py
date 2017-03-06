import logging
import cgroups_util
import time

logger = logging.getLogger('DOCKERSTATS')


def get_metrics(rootfs, interval, containers):
    metrics = {}

    mountpoints = cgroups_util.find_mountpoints(rootfs)
    _add_containers_cgroups(rootfs, mountpoints, containers)

    _add_containers_stats(rootfs, containers, "prev_stats")
    time.sleep(interval)
    _add_containers_stats(rootfs, containers, "now_stats")

    for container in containers:
        finger = container.get("finger")
        now_stats = container.get("now_stats")
        prev_stats = container.get("prev_stats")

        container_metrics = _get_container_metrics(finger, now_stats, prev_stats, interval)
        metrics.update(container_metrics)

    return metrics


def _add_containers_cgroups(rootfs, mountpoints, containers):
    for container in containers:
        pid = container.get("pid")
        cgroups = cgroups_util.find_container_cgroups(rootfs, mountpoints, pid)
        container["cgroups"] = cgroups


def _add_containers_stats(rootfs, containers, key):
    for container in containers:
        stats = _get_container_stats(rootfs, container)
        container[key] = stats


def _get_container_stats(rootfs, container):
    cgroups = container.get("cgroups")
    pid = container.get("pid")

    stats = {
        "network": cgroups_util.get_net_stats(rootfs, pid),
        "disk": cgroups_util.get_blkio_stats(cgroups["blkio"], pid),
        "cpu": cgroups_util.get_cpu_stats(rootfs, cgroups["cpuacct"], pid),
        "memory": cgroups_util.get_memory_stats(rootfs, cgroups["memory"], pid),
    }

    return stats


def _get_container_metrics(finger, now_stats, prev_stats, interval):
    base_path = finger + '.base'
    metrics = {base_path + '.count': 1}

    metrics.update(_get_disk_metrics(base_path, now_stats.get("disk"), prev_stats.get("disk"), interval))
    metrics.update(_get_cpu_metrics(base_path, now_stats.get("cpu"), prev_stats.get("cpu"), interval))
    metrics.update(_get_memory_metrics(base_path, now_stats.get("memory")))
    metrics.update(_get_network_metrics(base_path, now_stats.get("network"), prev_stats.get("network"), interval))

    return metrics


"""
disk metrics
"""


def _get_disk_metrics(base_path, now_stats, prev_stats, interval):
    disk_path = base_path + '.disk'
    metrics = {}

    for metric, value in now_stats.iteritems():
        path = disk_path + '.' + metric
        per_sec_path = path + '_per_sec'

        metrics[path] = value
        metrics[per_sec_path] = (float(value) - float(prev_stats.get(metric))) / interval

    return metrics


"""
cpu metrics
"""


def _get_cpu_metrics(base_path, now_stats, prev_stats, interval):
    cpu_path = base_path + '.cpu'
    num_cores = now_stats.get('cores')

    system_percent, user_percent, usage_percent = 0.0, 0.0, 0.0
    total_delta = now_stats.get('total') - prev_stats.get('total')

    if total_delta > 0:
        total_delta_per_sec = float(total_delta) / interval

        usage_delta = now_stats.get('usage') - prev_stats.get('usage')
        if usage_delta > 0:
            usage_delta_per_sec = float(usage_delta) / interval
            usage_percent = usage_delta_per_sec / total_delta_per_sec * num_cores * 100

        system_delta = now_stats.get("system") - prev_stats.get('system')
        if system_delta > 0:
            system_delta_per_sec = float(system_delta) / interval
            system_percent = system_delta_per_sec / total_delta_per_sec * num_cores * 100

        user_delta = now_stats.get('user') - prev_stats.get('user')
        if user_delta > 0:
            user_delta_per_sec = float(user_delta) / interval
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
    memory_path = base_path + '.vmem'

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


def _get_network_metrics(base_path, now_stats, prev_stats, interval):
    network_path = base_path + '.network'
    metrics = {}

    for metric, value in now_stats.iteritems():
        path = network_path + '.' + metric
        per_sec_path = path + '_per_sec'

        metrics[path] = value
        metrics[per_sec_path] = (float(value) - float(prev_stats.get(metric))) / interval

        if metric == 'bytes_recv':
            metrics[base_path + '.net_download'] = metrics[per_sec_path] / 1024

        elif metric == 'bytes_sent':
            metrics[base_path + '.net_upload'] = metrics[per_sec_path] / 1024

    return metrics
