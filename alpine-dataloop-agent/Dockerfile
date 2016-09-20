FROM smebberson/alpine-base:2.0.0
MAINTAINER Tom Ashley <tom@dataloop.io>

# Install dataloop basic requirements
RUN apk add --no-cache --update bash curl python python-dev py-pip gcc musl-dev linux-headers

ADD agent/ /dataloop-agent
ADD root/ /

# install pip requirements and make necessary dirs
RUN pip install -r /dataloop-agent/requirements.txt && mkdir -p /etc/dataloop /var/log/dataloop /opt/dataloop

# add run scripts

# compile and cleanup/remove py files for pyc ?


# cleanup
RUN apk del python-dev gcc linux-headers

# expose the fingerprint
EXPOSE 8000
