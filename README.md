# Outlyer (Dataloop) docker containers repository

This repository contains a set of containers built by Outlyer to aid in monitoring docker environments.

## agent

This is the outlyer agent container that will discover and monitor docker containers on a host.

https://hub.docker.com/r/outlyer/agent/


## dataloop-docker

This container is deprecated in favour of the agent container above


## mongodb_exporter

This container runs the Prometheus exporter for MySQL server metrics and an Outlyer (Dataloop) agent instance to collect the metrics and send them into Outlyer.

## mysqld_exporter

This container runs the Prometheus exporter for MySQL server metrics and an Outlyer (Dataloop) agent instance to collect the metrics and send them into Outlyer.
