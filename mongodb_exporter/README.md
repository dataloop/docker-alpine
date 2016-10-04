DATALOOP/MONGODB_EXPORTER
========================

This container runs the Prometheus exporter for MySQL server metrics and a Dataloop agent instance to collect the metrics and send them into Dataloop.

This container is built on [dataloop/agent-base](https://github.com/dataloop/docker-alpine/agent/base)

This container uses the [3rd party Prometheus exporter](https://github.com/dcu/mongodb_exporter) from dcu.


USAGE
=====

In it's simplest form, you must pass this container a `DATALOOP_AGENT_KEY` for the Dataloop agent and a `DATA_SOURCE_NAME` for the mongodb_exporter to connect to a database instance.

Pass any options for the mongodb_exporter in a string to the `EXPORTER_OPTIONS` environment variable.

```
docker run -d \
  -e "EXPORTER_OPTION=" \
  -p 8000:8000 \
  -e "DATALOOP_AGENT_KEY=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" \
  -p 9100:9100 \
  dataloop/mongodb_exporter:latest
```


The Dataloop Agent finger print is available on the container port 8000

The mongodb_exporter Prometheus endpoint is on the container port 9100


ENVIRONMENT VARIABLES
=====================

See https://github.com/dataloop/docker-alpine/agent/base for extra options to be passed for the Dataloop agent.


DATALOOP PLUGIN
===============

This container will require a plugin in Dataloop to make it useful

This is sufficiently basic to copy into a plugin and apply to this container directly, or via a tag.

The plugin type *must* be set to `prometheus`

```
#!/usr/bin/env python

import requests

print requests.get('http://localhost:9100/metrics').text
```


EXTRA INFORMATION
=================

* [Prometheus Exporter Documentation](https://github.com/prometheus/mysqld_exporter)
* [Learn more about Prometheus exporters](https://prometheus.io/docs/instrumenting/exporters/)
