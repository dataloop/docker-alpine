FROM dataloop/agent-base:latest
MAINTAINER Tom Ashley <tom@dataloop.io>

RUN curl -L -k https://github.com/dataloop/mongodb_exporter/releases/download/760287c/mongodb_exporter -o /bin/mongodb_exporter

ADD root /

EXPOSE 9001
