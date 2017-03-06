Dataloop Docker Autodiscovery Container
=======================================

This container contains a Dataloop agent and some magic scripts that create virtual agents in Dataloop for each
running container. Depending on which OS you are running on your Docker hosts you may need to add different run options.

This container builds on [dataloop/agent-base](https://github.com/dataloop/docker-alpine/tree/master/agent-base) where further options to pass to the container can be found.

The list of metrics returned for each running containers can be found [here](https://github.com/dataloop/docker-alpine/tree/master/dataloop-docker/METRICS.md).

## Most Linuxes

```
DATALOOP_AGENT_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DATALOOP_NAME=docker_container_name

docker run -d \
-e "DATALOOP_AGENT_KEY=${DATALOOP_AGENT_KEY}" \
-e "DATALOOP_NAME=${DATALOOP_NAME}" \
-v /var/run/docker.sock:/var/run/docker.sock:ro \
-v /proc:/rootfs/proc:ro \
-v /sys/fs/cgroup:/rootfs/sys/fs/cgroup:ro \
dataloop/dataloop-docker:latest
```

## Amazon Linux

If using an Amazon Linux AMI you will need to change the /cgroup volume mount location

```
DATALOOP_AGENT_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DATALOOP_NAME=docker_container_name

docker run -d \
-e "DATALOOP_AGENT_KEY=${DATALOOP_AGENT_KEY}" \
-e "DATALOOP_NAME=${DATALOOP_NAME}" \
-v /var/run/docker.sock:/var/run/docker.sock:ro \
-v /proc:/rootfs/proc:ro \
-v /cgroup:/rootfs/sys/fs/cgroup:ro \
dataloop/dataloop-docker:latest
```

# Troubleshooting

If you dont see any memory metrics in your containers you will need to enable memory accounting in cgroups. To do that just add some kernel command-line parameters: cgroup_enable=memory swapaccount=1. More info from the [docker documentation](https://docs.docker.com/engine/admin/runmetrics/#/memory-metrics-memorystat).

Proxy
=====

If you are behind a proxy server, you can pass the standard proxy environment variables to the docker container to have data passed through:

```
docker run -e HTTP_PROXY=http://proxy:port....
```


Contributing Changes
====================

If you want to modify the container then feel free to submit a pull request. Below is the spec for what each script does.

A set of independent foreground processes that log to standard out that can be run under a [s6-svc](http://skarnet.org/software/s6/)

All state is stored in Dataloop so these scripts can be run in ephemeral containers with no local storage.

- agents.py

Polls Docker api and Dataloop. Ensures containers match agents via register and deregister API's. Tag containers with relevant info taken from various places. Send a ping metric for each running containers.

- metrics.py

Sends docker metrics to Dataloop via the Graphite endpoint every 30 seconds by matching container ID to agent name.
