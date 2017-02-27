### Docker Metrics
==================

Note: It looks like some linux distributions don't enable metrics cgroups by default. From [docker docs](https://docs.docker.com/engine/admin/runmetrics/#/memory-metrics-memorystat): "To enable it, all you have to do is to add some kernel command-line parameters: cgroup_enable=memory swapaccount=1."


#### base

- count
- memory
- swap
- cpu
- net_upload
- net_download

#### base.vmem

- active
- available
- available_gb
- cached
- inactive
- percent
- total
- total_gb
- used
- used_gb

#### base.network

- bytes_recv
- bytes_recv_per_sec
- bytes_sent
- bytes_sent_per_sec
- dropin
- dropin_per_sec
- dropout
- dropout_per_sec
- errin
- errin_per_sec
- errout
- errout_per_sec
- packets_recv
- packets_recv_per_sec
- packets_sent
- packets_sent_per_sec

#### base.disk

- read_bytes
- read_bytes_per_sec
- read_count
- read_count_per_sec
- write_bytes
- write_bytes_per_sec
- write_count
- write_count_per_sec


#### base.cpu

- cores
- system
- user
