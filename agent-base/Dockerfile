FROM smebberson/alpine-base:3.1.0
MAINTAINER Tom Ashley <tom@dataloop.io>

ADD agent /opt/dataloop/agent

RUN apk add --no-cache --update \
      bash \
      curl \
      python \
      python-dev \
      py-pip \
      gcc \
      musl-dev \
      linux-headers \
      libffi-dev \
      openssl-dev \
      py-mysqldb \
      py-psycopg2 \
      && \

    rm -rf /usr/share && \

    pip --no-cache-dir install -r /opt/dataloop/agent/requirements.txt && \

    mkdir -p /etc/dataloop /var/log/dataloop && \

    sed -i '/MySQL-python/d' /opt/dataloop/agent/plugin_requirements.txt && \
    sed -i '/psycopg2/d' /opt/dataloop/agent/plugin_requirements.txt && \

    pip --no-cache-dir install -r /opt/dataloop/agent/plugin_requirements.txt && \

    python -m compileall /usr/lib/python2.7 || true && \
    find /usr/lib/python2.7 -type f -name "*.py" -delete && \
    find /usr/lib/python2.7 -type f -name "*.po" -delete && \

    /usr/bin/python -m compileall /opt/dataloop/agent && \
    find /opt/dataloop/agent/dataloop_agent \
      -path /opt/dataloop/agent/dataloop_agent/__init__.py \
      -prune -o -name '*py' -print -exec rm -fv {} \; && \


    apk del \
      python-dev \
      py-pip \
      gcc \
      musl-dev \
      linux-headers \
      libffi-dev \
      openssl-dev

# add run scripts
ADD root/ /

# expose the fingerprint
EXPOSE 8000
