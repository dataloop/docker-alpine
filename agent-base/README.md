DATALOOP/AGENT-BASE
==============

This container is provided as a base container running a minimal dataloop-agent.

Based upon [Alpine Linux](https://www.alpinelinux.org) and using [Scott Mebberson](https://github.com/smebberson) base image, [s6](http://skarnet.org/software/s6/) is used for process managment

Please see [here](https://github.com/smebberson/docker-alpine) for more information about Scott Mebberson's base images and design.


USAGE
=====

In it's simplest form, you need only pass the API Key for your Dataloop account to the docker image.

```
docker run -d \
  -e "DATALOOP_AGENT_KEY=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" \
  dataloop/agent-base:latest
```

ENVIRONMENT VARIABLES
=====================

This docker image will accept various other environment variables to allow you to customize the configuration for the dataloop-agent

`DATALOOP_AGENT_KEY` *Required* The API Key for your Dataloop account. *Default*: None

`DATALOOP_NAME` *Optional* A name for your agent to appear as in Dataloop. *Default*: dataloop

`DATALOOP_TAGS` *Optional* A comma separated list of tags to apply to the agent. *Default*: docker

`DATALOOP_FINGERPRINT` *Optional* You can pass an existing fingerprint if you want to keep your data association in Dataloop. *Default* None

`DATALOOP_DEBUG` *Optional* You can pass in the debug flag `yes/no` or `true/false` to add extra logging to the agent. *Default* no


EXPOSED PORTS
=============

Port 8000 is exposed as an HTTP endpoint. It will respond to GET with the fingerprint of the Dataloop agent.

```
curl -XGET http://<container>:8000
```

EXTENDING
=========

This container is designed to be extended. 

Use it as a base to add your software and have Dataloop monitor from within your container.

See how we are using it with our other containers found [here](https://github.com/dataloop/docker-alpine)
