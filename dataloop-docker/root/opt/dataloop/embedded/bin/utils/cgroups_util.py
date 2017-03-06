import os
import logging
from collections import defaultdict

logger = logging.getLogger('CGROUPS')

cgroup_subsystems = ["memory", "cpuacct", "blkio"]

software_clock = os.sysconf_names['SC_CLK_TCK']
ticks_per_second = os.sysconf(software_clock)

nanoseconds_per_second = 1000000000


def _bytes_to_gb(num):
    return round(float(num) / 1024 / 1024 / 1024, 2)


def _ticks_to_nanoseconds(num):
    return num * nanoseconds_per_second / ticks_per_second


"""
cgroups
"""


def find_mountpoints(rootfs):
    """Read /proc/mounts and find where the cgroups subsystems we are interested in are mounted.

    format of /proc/mounts:
    ex: "memory /rootfs/sys/fs/cgroup/memory cgroup rw,nosuid,nodev,noexec,relatime,memory 0 0"
    - 1st column specifies the device that is mounted.
    - 2nd column reveals the mount point.
    - 3rd column tells the file-system type.
    - 4th column tells you if it is mounted read-only (ro) or read-write (rw).
    - 5th and 6th columns are dummy values designed to match the format used in /etc/mtab

    get_mountpoints will return something like:
    {
        'blkio': '/rootfs/sys/fs/cgroup/blkio',
        'cpuacct': '/rootfs/sys/fs/cgroup/cpu,cpuacct',
        'memory': '/rootfs/sys/fs/cgroup/memory'
    }
    """
    mountpoints = {}
    mount_path = os.path.join(rootfs, "/proc/mounts")
    logger.debug("finding mounted cgroups in %s" % mount_path)

    with open(mount_path) as fp:
        mounts = map(lambda x: x.split(), fp.read().splitlines())

    cgroup_mounts = filter(lambda x: x[2] == "cgroup" and os.path.exists(x[1]), mounts)

    # only keep the host cgroups mounts
    rootfs_mounts = filter(lambda x: x[1].startswith(rootfs), cgroup_mounts)

    # old cgroup style, add the rootfs path manually
    if not(rootfs_mounts):
        for mount in cgroup_mounts:
            mount[1] = os.path.join(rootfs, mount[1][1:])
            rootfs_mounts.append(mount)

    # find the subsystems we are interested in
    for _, mountpoint, _, opts, _, _ in rootfs_mounts:
        for opt in opts.split(','):
            if opt in cgroup_subsystems:
                mountpoints[opt] = mountpoint

    if not(mountpoints):
        logger.error("can't find mounted cgroups in %s" % mount_path)

    return mountpoints


def find_container_cgroups(rootfs, mountpoints, pid):
    """Read /proc/<pid>/cgroup to find the relative container cgroups paths.

    add them to the corresponding mountpoint to get the full path:
    {
        'blkio': '/rootfs/sys/fs/cgroup/blkio/docker/container_id',
        'cpuacct': '/rootfs/sys/fs/cgroup/cpu,cpuacct/docker/container_id',
        'memory': '/rootfs/sys/fs/cgroup/memory/docker/'container_id'
    }
    """
    cgroups = {}
    proc_path = os.path.join(rootfs, 'proc', str(pid), 'cgroup')
    logger.debug("reading process cgroups path in %s" % proc_path)

    with open(proc_path, 'r') as fp:
        lines = map(lambda x: x.split(':'), fp.read().splitlines())

        # get a dict cgroup/path, remove the first '/' from the path for os.path.join
        names = map(lambda x: x[1], lines)
        paths = map(lambda x: x[2] if x[2][0] != '/' else x[2][1:], lines)
        subsystems = dict(zip(names, paths))

    for names, path in subsystems.items():

        # sometimes multiple cgroups are grouped in here, like cpu,cpuacct
        for cgroup in names.split(','):
            if cgroup in cgroup_subsystems:
                cgroups[cgroup] = os.path.join(mountpoints[cgroup], path)

    if not(cgroups):
        logger.error("can't find container cgroups in %s" % proc_path)

    return cgroups


"""
memory stats
"""


def get_memory_stats(rootfs, cgroup_path, pid):
    memory_stats = {}

    try:
        host_stats = _parse_host_memory_file(rootfs)
        proc_stats = _parse_memory_stat_file(cgroup_path)

        memory_stats = _format_memory_stats(proc_stats, host_stats)

    except Exception as ex:
        logger.error("process %s - memory metrics will be missing: %s" % (pid, ex), exc_info=True)

    return memory_stats


# note: values in /proc/meminfo are set in kb
def _parse_host_memory_file(rootfs):
    host_memory = {}
    host_memory_path = os.path.join(rootfs, "/proc/meminfo")
    logger.debug("finding host memory info in %s" % host_memory_path)

    with open(host_memory_path, 'r') as fp:
        lines = fp.readlines()

    for line in lines:
        cols = line.split(':')
        if cols[0] == 'MemTotal':
            total = cols[1].strip().split(' ')[0]
            host_memory["total"] = int(total) * 1024
        elif cols[0] == "SwapTotal":
            swap = cols[1].strip().split(' ')[0]
            host_memory["swap"] = int(swap) * 1024

    if not host_memory:
        logger.error("can't find host memory info in %s" % host_memory_path)

    return host_memory


def _parse_memory_stat_file(cgroup_path):
    stats = {}
    stat_path = os.path.join(cgroup_path, "memory.stat")
    logger.debug("finding memory stats in %s" % stat_path)

    with open(stat_path, 'r') as fp:
        lines = fp.read().splitlines()

    stats = dict(map(lambda x: x.split(' ', 1), lines))
    stats = {k: int(v) for k, v in stats.items()}

    if not stats:
        logger.error("can't find memory stats in %s" % stat_path)

    return defaultdict(int, stats)


def _format_memory_stats(stats, host_memory):
    # if the container has no memory limit, use the host memory instead
    mem_limit = stats.get("hierarchical_memory_limit")
    if mem_limit > host_memory.get("total", 0):
        mem_limit = host_memory.get("total", 0)

    swap_limit = stats.get("hierarchical_memsw_limit")
    if swap_limit > host_memory.get("swap", 0):
        swap_limit = host_memory.get("swap", 0)

    mem_used = stats.get('rss') + stats.get('cache') + stats.get('swap')

    mem_percent = round(float(mem_used) / float(mem_limit) * 100.0, 2) if mem_limit else None
    swap_percent = round(float(stats.get("swap")) / float(swap_limit) * 100.0, 2) if swap_limit else None

    stats = {
        "used": mem_used,
        "total": mem_limit,
        "available": mem_limit - stats.get('rss'),
        "memory": mem_percent,
        "swap": swap_percent,
        "cached": stats.get("cache"),
        "active": stats.get("active_file") + stats.get("active_anon"),
        "inactive": stats.get("inactive_file") + stats.get("inactive_anon"),
    }

    for key in ["used", "total", "available"]:
        stat = key + "_gb"
        stats[stat] = _bytes_to_gb(stats[key])

    return stats


"""
blkio stats
"""


def get_blkio_stats(cgroup_path, pid):
    blkio_stats = {}

    try:
        blkio_stats.update(_parse_blkio_file(cgroup_path, "throttle.io_serviced", "count"))
        blkio_stats.update(_parse_blkio_file(cgroup_path, "throttle.io_service_bytes", "bytes"))

    except Exception as ex:
        logger.error("process %s - disk metrics will be missing: %s" % (pid, ex), exc_info=True)

    return blkio_stats


def _parse_blkio_file(cgroup_path, file_name, uom):
    stats = defaultdict(int)
    stat_path = os.path.join(cgroup_path, "blkio." + file_name)
    logger.debug("finding disk stats in %s" % stat_path)

    with open(stat_path, 'r') as fp:
        lines = fp.read().splitlines()

    for line in lines:
        if 'Read' in line:
            metric_name = "read_" + uom
            stats[metric_name] += int(line.split()[2])
        if 'Write' in line:
            metric_name = "write_" + uom
            stats[metric_name] += int(line.split()[2])

    if not(stats):
        logger.error("can't find disk stats in %s" % stat_path)

    return stats


"""
cpu stats
"""


def get_cpu_stats(rootfs, cgroup_path, pid):
    cpu_stats = {}

    try:
        cpu_stats["usage"] = _parse_cpu_usage_file(cgroup_path)
        cpu_stats["cores"] = len(_parse_usage_percpu_file(cgroup_path))
        cpu_stats["total"] = _parse_cpu_total_file(rootfs)
        cpu_stats.update(_parse_cpu_stat_file(cgroup_path))

    except Exception as ex:
        logger.error("process %s - cpu metrics will be missing: %s" % (pid, ex), exc_info=True)

    return cpu_stats


def _parse_cpu_usage_file(cgroup_path):
    usage = 0
    stat_path = os.path.join(cgroup_path, "cpuacct.usage")
    logger.debug("finding usage stat in %s" % stat_path)

    path = os.path.join(cgroup_path, "cpuacct.usage")
    with open(path, 'r') as fp:
        line = fp.readline()
        if line:
            usage = int(line)

    if not(usage):
        logger.error("can't find usage stat in %s" % stat_path)

    return usage


def _parse_usage_percpu_file(cgroup_path):
    usage_per_cpu = []
    stat_path = os.path.join(cgroup_path, "cpuacct.usage_percpu")
    logger.debug("finding usage per cpu stats in %s" % stat_path)

    with open(stat_path, 'r') as fp:
        line = fp.readline()
        if line:
            usage_per_cpu = line.strip().split(' ')

    if not(usage_per_cpu):
        logger.error("can't find usage per cpu stats in %s" % stat_path)

    return usage_per_cpu


def _parse_cpu_total_file(rootfs):
    total = 0
    stat_path = os.path.join(rootfs, 'proc/stat')
    logger.debug("finding cpu total stat in %s" % stat_path)

    with open(stat_path, 'r') as fp:
        lines = fp.readlines()

    for l in lines:
        cols = l.split(' ')
        if str(cols[0]).strip() == 'cpu':
            total = sum(int(c) for c in cols[2:10])
            total = _ticks_to_nanoseconds(total)

    if not(total):
        logger.error("can't find cpu total stat in %s" % stat_path)

    return total


def _parse_cpu_stat_file(cgroup_path):
    cpu_stats = {"user": 0, "system": 0}
    stat_path = os.path.join(cgroup_path, "cpuacct.stat")
    logger.debug("finding cpu stats in %s" % stat_path)

    with open(stat_path, 'r') as fp:
        stats = dict(map(lambda x: x.split(' ', 1), fp.read().splitlines()))

    if stats:
        cpu_stats['user'] = _ticks_to_nanoseconds(int(stats.get('user')))
        cpu_stats['system'] = _ticks_to_nanoseconds(int(stats.get('system')))
    else:
        logger.error("can't find cpu stats in %s" % stat_path)

    return cpu_stats


"""
network stats
"""


def get_net_stats(rootfs, pid):
    net_stats = {}

    try:
        net_dev_stats = _parse_net_file(rootfs, pid)
        eth0_stats = net_dev_stats.get("eth0", [])

        if eth0_stats:
            net_stats = _format_net_stats(eth0_stats)

    except Exception as ex:
        logger.error("process %s - network metrics will be missing: %s" % (pid, ex), exc_info=True)

    return net_stats


def _parse_net_file(rootfs, pid):
    """Read the proc net stat file in /proc/<pid>/net/dev.

    net stats can be found in this specific order in that file:
    [
        bytes, packets, errs, drop, fifo, frame, compressed, multicast      # receive
        bytes, packets, errs, drop, fifo, colls, carrier, compressed        # transmit
    ]
    """
    net_stats = {}
    stat_path = os.path.join(rootfs, 'proc', str(pid), 'net/dev')
    logger.debug("finding net stats in %s" % stat_path)

    with open(stat_path, 'r') as fp:
        lines = fp.readlines()

    # the first two lines are headers, we can skip them
    for l in lines[2:]:
        cols = l.split(':', 1)
        interface_name = str(cols[0]).strip()
        interface_stats = cols[1].split()
        net_stats[interface_name] = interface_stats

    if not(net_stats):
        logger.error("can't find net stats in %s" % stat_path)

    return net_stats


def _format_net_stats(stats):
    net_stats_map = {
        "bytes_recv": 0,
        "packets_recv": 1,
        "errin": 2,
        "dropin": 3,
        "bytes_sent": 8,
        "packets_sent": 9,
        "errout": 10,
        "dropout": 11,
    }

    net_stats = {}
    for name, index in net_stats_map.items():
        net_stats[name] = int(stats[index])

    return net_stats
