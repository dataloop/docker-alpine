# OUTLYER/AGENT Autodiscovery Container

This container contains a Dataloop (Outlyer) agent. It will create virtual agents in Outlyer for each running container. Depending on which OS you are running on your Docker hosts you may need to add different run options.

The list of metrics returned for each running containers can be found [here](https://github.com/dataloop/docker-alpine/tree/master/agent/METRICS.md).

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
outlyer/agent:latest
```

## Amazon Linux (ECS)

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
outlyer/agent:latest

```

## CentOS 6

CentOS 6 supports Docker to version 1.7, whereat the platform appears to have been deprecated.

You can still run this container, if you install cgroups and adjust the volume mapping for the cgroups directory.

```
sudo yum install -y libcgroup
```

CentOS 6 has cgroups under `/cgroups`. Run the container accordingly

```
DATALOOP_AGENT_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DATALOOP_NAME=docker_container_name

docker run -d \
-e "DATALOOP_AGENT_KEY=${DATALOOP_AGENT_KEY}" \
-e "DATALOOP_NAME=${DATALOOP_NAME}" \
-v /var/run/docker.sock:/var/run/docker.sock:ro \
-v /proc:/rootfs/proc:ro \
-v /cgroup:/rootfs/sys/fs/cgroup:ro \
outlyer/agent:latest

```

## Support Versions

This container has been tested to run on Docker >= 1.7


## Troubleshooting

Please contact us on <https://slack.outlyer.com> or [support[at]outlyer.com](mailto:support[at]outlyer.com) for help.

If you dont see any memory metrics in your containers you will need to enable memory accounting in cgroups. To do that just add some kernel command-line parameters: cgroup_enable=memory swapaccount=1. More info from the [docker documentation](https://docs.docker.com/engine/admin/runmetrics/#/memory-metrics-memorystat).

When running the agent with the above `docker run` options, some features will be missing. Please run the container with `--net host` if you would like the following features:

    - CPU load average for your containers
    - Container network connections
    - Host network metrics sent under your agent container

If you'd like to have host network metrics sent under your agent container (rather than your actual container's network metrics) and you cannot run your container with `--net host`, please follow these steps:

    1. Mount your host's sys folder on your agent container (e.g. pass `-v /sys:/rootfs/sys` to `docker run`);
    2. On your account's main overview page <https://app.outlyer.com/YOUR_ORG/YOUR_ACCOUNT/#/setup/overview>, click on "Setup Monitoring";
    3. Click on "Plugins List", then on "base.py".
    4. On the code editor, there should be a function called `check_netio`.
       Replace it with the one here: <https://gist.github.com/alexdias/d51ef12d02d9e8f56721c48d52517f5c>
    5. Click `Save changes` to have your base plugin updated.

## Proxy

If you are behind a proxy server, you can pass the standard proxy environment variables to the docker container to have data passed through:

```
docker run -e HTTP_PROXY=http://proxy:port....
```

## Environment Variables

This docker image will accept various other environment variables to allow you to customize the configuration for the dataloop-agent

`DATALOOP_AGENT_KEY` *Required* The API Key for your Dataloop account. *Default*: None

`DATALOOP_NAME` *Optional* A name for your agent to appear as in Dataloop. *Default*: dataloop

`DATALOOP_TAGS` *Optional* A comma separated list of tags to apply to the agent. *Default*: docker

`DATALOOP_FINGERPRINT` *Optional* You can pass an existing fingerprint if you want to keep your data association in Dataloop. *Default* None

`DATALOOP_DEBUG` *Optional* You can pass in the debug flag `yes/no` or `true/false` to add extra logging to the agent. *Default* no


## Exposed Ports

Port 8000 is exposed as an HTTP endpoint. It will respond to GET with the fingerprint of the Dataloop agent.

```
curl -XGET http://<container>:8000
```

## Contributing Changes

If you want to modify the container then feel free to submit a pull request. Below is the spec for what each script does.

A set of independent foreground processes that log to standard out that can be run under a [s6-svc](http://skarnet.org/software/s6/)

This container is also provided as a base container running a Dataloop agent. You can extend it with embedded plugins, or with Prometheus exporters, for example.

Based upon [Alpine Linux](https://www.alpinelinux.org) and using [Scott Mebberson](https://github.com/smebberson) base image, [s6](http://skarnet.org/software/s6/) is used for process managment

Please see [here](https://github.com/smebberson/docker-alpine) for more information about Scott Mebberson's base images and design.
