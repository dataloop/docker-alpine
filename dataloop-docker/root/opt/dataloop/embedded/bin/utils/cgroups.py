import os
import logging
from collections import defaultdict

logger = logging.getLogger('CGROUPS')

cgroup_hierarchies = ["memory", "cpuacct", "blkio"]
software_clock = os.sysconf_names['SC_CLK_TCK']

ticks_per_second = os.sysconf(software_clock)
nanoseconds_per_second = 1000000000


def get_mountpoints(rootfs):
    """read /proc/mounts and find the mountpoints for the cgroup hierarchies we are
    interested in, eg:
    {
        'blkio': '/rootfs/sys/fs/cgroup/blkio',
        'cpuacct': '/rootfs/sys/fs/cgroup/cpu,cpuacct',
        'cpu': '/rootfs/sys/fs/cgroup/cpu,cpuacct',
        'memory': '/rootfs/sys/fs/cgroup/memory'
    }
    """

    mountpoints = {}

    mount_path = os.path.join(rootfs, "/proc/mounts")
    logger.debug("reading mounted cgroups in %s" % mount_path)

    with open(mount_path) as fp:
        mounts = map(lambda x: x.split(), fp.read().splitlines())

    def filter_mountpoint(mount):
        return mount[2] == "cgroup" and \
        mount[1].startswith(rootfs) and \
        os.path.exists(mount[1])

    cgroup_mounts = filter(filter_mountpoint, mounts)

    for _, mountpoint, _, opts, _, _ in cgroup_mounts:
        for opt in opts.split(','):
            if opt in cgroup_hierarchies:
                mountpoints[opt] = mountpoint

    if not(mountpoints):
        logger.error("can't find mounted cgroups in %s" % mount_path)

    return mountpoints


def find_container_cgroups(rootfs, mountpoints, container):
    """find the containers stat file path, in /proc/<pid>/cgroup we get something like:
    {
        'blkio': '/docker/8db99f06d12e7a4d6a7a6a0e46a94467b1af695286d1aa422e65fa59c1b5b048',
        'cpuacct': '/docker/8db99f06d12e7a4d6a7a6a0e46a94467b1af695286d1aa422e65fa59c1b5b048',
        'cpu': '/docker/8db99f06d12e7a4d6a7a6a0e46a94467b1af695286d1aa422e65fa59c1b5b048',
        'memory': /docker/'8db99f06d12e7a4d6a7a6a0e46a94467b1af695286d1aa422e65fa59c1b5b048'
    }
    then we just have to concatenate it with the right mountpoint """

    cgroups = {}
    pid = container.attrs.get('State', {}).get('Pid', None)

    proc_path = os.path.join(rootfs, 'proc', str(pid), 'cgroup')
    logger.debug("reading process cgroups path in %s" % proc_path)

    with open(proc_path, 'r') as fp:
        lines = map(lambda x: x.split(':'), fp.read().splitlines())
        subsystems = dict(zip(map(lambda x: x[1], lines), map(lambda x: x[2] if x[2][0] != '/' else x[2][1:], lines)))

    for names, path in subsystems.items():
        for cgroup in names.split(','):
            if cgroup in cgroup_hierarchies:
                cgroups[cgroup] = os.path.join(mountpoints[cgroup], path)

    if not(cgroups):
        logger.error("can't find container cgroups in %s" % proc_path)

    return cgroups


"""
memory stats
"""

def get_memory_stats(rootfs, cgroup_path):
    host_memory = _parse_host_memory_file(rootfs)
    stats = _parse_cgroup_file(cgroup_path, "memory.stat")

    return _format_memory_metrics(stats, host_memory)


def _format_memory_metrics(stats, host_memory):
    mem_used = int(stats.get('rss'), 0) + int(stats.get('cache', 0)) + int(stats.get('swap', 0))

    metrics = {
        "used":     mem_used,
        "used_gb":  _bytes_to_gb(mem_used),
        "cached":   stats.get("cache"),
    }

    if  "active_file" in stats and "active_anon" in stats:
        metrics['active'] = int(stats.get("active_file")) + int(stats.get("active_anon"))

    if "inactive_file" in stats and "inactive_anon" in stats:
        metrics['inactive'] = int(stats.get("inactive_file")) + int(stats.get("inactive_anon"))


    # if the container has no memory limit, use host memory instead
    mem_limit = stats.get("hierarchical_memory_limit")
    if mem_limit > host_memory.get("total"):
        mem_limit = host_memory.get("total") or None

    swap_limit = stats.get("hierarchical_memsw_limit")
    if swap_limit > host_memory.get("swap"):
        swap_limit = host_memory.get("swap") or None

    if mem_limit:
        mem_limit = mem_limit * 1024
        metrics["total"] = mem_limit
        metrics["total_gb"] = _bytes_to_gb(mem_limit)
        metrics["available"] = int(mem_limit) - mem_used
        metrics["available_gb"] = _bytes_to_gb(metrics["available"])

        memory = float(mem_used) / float(mem_limit) * 100.0
        metrics["memory"] = round(memory, 2)

    if swap_limit:
        swap_limit = swap_limit * 1024
        swap = float(stats.get("swap", 0)) / float(swap_limit)
        metrics["swap"] = round(swap, 2)

    return metrics

def _parse_host_memory_file(rootfs):
    host_memory = {}

    try:
        path = os.path.join(rootfs, "/proc/meminfo")
        with open(path, 'r') as fp:
            lines = fp.readlines()

            for l in lines:
                cols = l.split(':')
                name =  str(cols[0]).strip()
                if name == 'MemTotal':
                    host_memory["total"] = int(cols[1].strip().split(' ')[0])
                elif name == "SwapTotal":
                    host_memory["swap"] = int(cols[1].strip().split(' ')[0])

            return host_memory

    except IOError:
        logger.warn("can't open %s. metrics will be missing" % path)
        return host_memory



"""
blkio stats
"""

def get_blkio_stats(cgroup_path):
    metrics = {}

    metrics.update(_parse_blkio_file(cgroup_path, "blkio.throttle.io_serviced", "count"))
    metrics.update(_parse_blkio_file(cgroup_path, "blkio.throttle.io_service_bytes", "bytes"))

    return metrics


def _parse_blkio_file(cgroup_path, file_name, uom):
    try:
        path = os.path.join(cgroup_path, file_name)
        with open(path, 'r') as fp:
            metrics = defaultdict(int)
            stats = fp.read().splitlines()

            for line in stats:
                if 'Read' in line:
                    metric_name = "read_" + uom
                    metrics[metric_name] += int(line.split()[2])
                if 'Write' in line:
                    metric_name = "write_" + uom
                    metrics[metric_name] += int(line.split()[2])
            return metrics

    except IOError:
        logger.warn("can't open %s. metrics will be missing" % path)
        return {}


"""
cpu stats
"""


def get_cpu_stats(rootfs, cgroup_path):
    stats = {
        "usage": int(_parse_cpu_usage_file(cgroup_path))
    }

    usage_per_cpu = _parse_usage_percpu_file(cgroup_path)
    if usage_per_cpu:
        stats["cores"] = len(usage_per_cpu)

    cpu_stats =  _parse_cgroup_file(cgroup_path, "cpuacct.stat")
    if cpu_stats:
        stats['user'] = (int(cpu_stats.get('user')) * nanoseconds_per_second) / ticks_per_second
        stats['system'] = (int(cpu_stats.get('system')) * nanoseconds_per_second) / ticks_per_second

    total = _parse_cpu_total_file(rootfs)
    stats['total'] = total * nanoseconds_per_second / ticks_per_second

    return stats


def _parse_usage_percpu_file(cgroup_path):
    try:
        path = os.path.join(cgroup_path, "cpuacct.usage_percpu")
        with open(path, 'r') as fp:
            stats = fp.read().splitlines()
            return list(filter(None, stats[0].split(' ')))

    except IOError:
        logger.warn("can't open %s. metrics will be missing" % path)
        return []


def _parse_cpu_usage_file(cgroup_path):
    try:
        path = os.path.join(cgroup_path, "cpuacct.usage")
        with open(path, 'r') as fp:
            return fp.read().splitlines()[0]

    except IOError:
        logger.warn("can't open %s. metrics will be missing" % path)
        return None


def _parse_cpu_total_file(rootfs):
    total = 0

    try:
        stat_path = os.path.join(rootfs, 'proc/stat')
        with open(stat_path, 'r') as fp:
            lines = fp.readlines()

            for l in lines:
                cols = l.split(' ')
                if str(cols[0]).strip() == 'cpu':
                    total = sum(int(c) for c in cols[2:10])
            return total

    except IOError:
        logger.error("can't open %s. cpu metrics will be missing" % (stat_path))
        return total


"""
network stats
"""

# helper to map dataloop metric with /net/dev stat indexes
network_stats_map = {
    "bytes_recv":   0,
    "packets_recv": 1,
    "errin":        2,
    "dropin":       3,
    "bytes_sent":   8,
    "packets_sent": 9,
    "errout":       10,
    "dropout":      11,
}


def get_net_stats(rootfs, container):
    try:
        pid = container.attrs.get('State', {}).get('Pid', None)
        net_stats = _parse_net_file(rootfs, pid)

        # we only care about eth0 for now
        container_net_stats = net_stats.get("eth0", []) or []
        return _format_net_metrics(container_net_stats)

    except Exception:
        logger.error("container %s network metrics will be missing" % container.name)
        return {}


def _parse_net_file(rootfs, pid):
    """read the proc net stat file in /proc/<pid>/net/dev
    net stats can be found in this specific order in that file:
    [
        bytes, packets, errs, drop, fifo, frame, compressed, multicast      # receive
        bytes, packets, errs, drop, fifo, colls, carrier, compressed        # transmit
    ]
    """

    net_stats = {}
    net_stat_file = os.path.join(rootfs, 'proc', str(pid), 'net/dev')

    with open(net_stat_file, 'r') as fp:
        lines = fp.readlines()

        # the first two lines are headers, we can skip them
        for l in lines[2:]:
            cols = l.split(':', 1)
            interface_name = str(cols[0]).strip()
            interface_stats = cols[1].split()
            net_stats[interface_name] = interface_stats

        return net_stats


def _format_net_metrics(stats):
    net_metrics = {}

    for metric_name, index in network_stats_map.items():
        net_metrics[metric_name] = int(stats[index])

    return net_metrics


"""
utils
"""

def _parse_cgroup_file(cgroup_path, file_name):
    try:
        path = os.path.join(cgroup_path, file_name)
        with open(path, 'r') as fp:
            return dict(map(lambda x: x.split(' ', 1), fp.read().splitlines()))

    except IOError:
        logger.warn("can't open %s. metrics will be missing" % path)
        return {}


def _bytes_to_gb(num):
    return round(float(num) / 1024 / 1024 / 1024, 2)
