#!/usr/bin/env python
import sys
import os
import getopt
import requests
import uuid
import json
import grequests
from time import sleep
from socket import gethostname
from docker.client import Client
from docker.utils import kwargs_from_env


API_KEY = ''  # You need to set this!
EXCHANGE_URL = 'https://agent.dataloop.io'
API_URL = 'https://www.dataloop.io'
CADVISOR = 'http://127.0.0.1:8080'

# Don't touch anything below this point. In fact don't even scroll down.

if os.path.exists('/rootfs/var/run/docker.sock'):
    docker_cli = Client(base_url='unix://rootfs/var/run/docker.sock', version='auto')
else:
    docker_cli = Client(**kwargs_from_env(assert_hostname=False))


def api_header():
    return {"Content-type": "application/json", "Authorization": "Bearer " + API_KEY}


def get_mac():
    return requests.get(CADVISOR + '/api/v1.3/machine').json()['system_uuid']


def create_finger():
    return str(uuid.uuid4())


def agent_name_to_finger():
    agent_fingers = {}
    _resp = requests.get(API_URL + "/api/agents", headers=api_header()).json()
    for _agent in _resp:
        agent_fingers[_agent['name']] = _agent['id']
    return agent_fingers


def get_agents():
    agents = []
    _resp = requests.get(API_URL + "/api/agents", headers=api_header())
    if _resp.status_code == 200:
        for l in _resp.json():
            if l['mac'] == get_mac():
                agents.append(l['name'])
        return list(set(agents))


def get_agents_details(finger):
    _resp = requests.get(API_URL + "/api/agents/" + finger, headers=api_header())
    if _resp.status_code == 200:
        return json.loads(_resp.text)
    else:
        print "failed to get agent details"


def register_agent(finger, data):
    return requests.post(EXCHANGE_URL + '/agents/' + finger + '/register', json=data, headers=api_header())


def create_agent(container):
    _finger = create_finger()
    data = {
        'fingerprint': _finger,
        'tags': '',
        'name': container,
        'hostname': gethostname(),
        'mac': get_mac(),
        'os_name': 'docker',
        'os_version': '',
        'container': '',
        'processes': get_processes(container),
        'interfaces': get_network(container),
        'mode': 'solo',
        'version': '',
        'interpreter': ''
    }

    resp = register_agent(_finger, data)
    if resp.status_code == 200:
        print "successfully registered %s" % _finger
    else:
        print "registration of %s failed with status code %d" % (_finger, resp.status_code)


def de_register_agent(finger):
    requests.post(EXCHANGE_URL + '/agents/' + finger + '/deregister', headers=api_header())
    print "successfully deleted agent: %s" % finger


def ping(container_list, agent_fingers):
    rs = []
    for container in container_list:
        data = {
            'mac': get_mac(),
            'hostname': str(gethostname()),
            'tags': '',
            'os_name': 'docker',
            'os_version': '',
            'container_name': '',
            'proc_list': get_processes(container),
            'ip': '',
            'interfaces': get_network(container),
            'mode': 'solo',
            'name': str(container)
        }
        finger = agent_fingers[container]
        url = API_URL + '/api/agents/' + finger + '/ping'
        rs.append(grequests.post(url, json=data, headers=api_header()))
    return grequests.map(rs)

def get_containers():
    _containers = []
    _resp = requests.get(CADVISOR + '/api/v1.3/docker').json()
    for k, v in _resp.iteritems():
        if 'system.slice' in v['name']:
            _containers.append(v['name'].replace('/system.slice/docker-', '')[:12])
        else:
            _containers.append(v['name'].replace('/docker/', '')[:12])
    return _containers


def get_processes(container):
    process_list = []
    processes = docker_cli.top(container)['Processes']
    for process in processes:
        process_list.append(process[len(process) -1] + ':1')
    return process_list


def get_network(container):
    network_settings = docker_cli.inspect_container(container)['NetworkSettings']
    interface = [
        {
            'interface': 'eth0',
            'addresses': [
                {
                    'ips': [
                        network_settings['IPAddress']
                    ],
                    'family': 'AF_INET'
                }
            ]
        },
        {
            'interface': 'lo0',
            'addresses': [
                {
                    'ips': [
                        '127.0.0.1'
                    ],
                    'family': 'AF_INET'
                }
            ]
        }
    ]
    return interface


def sync():
    try:
        agents = []
        containers = []
        agent_fingers = agent_name_to_finger()

        agents = get_agents()
        containers = get_containers()

        # add agents that don't exist
        for container in containers:
            if container not in agents:
                print "adding container: %s" % container
                create_agent(container)

        # ping running containers
        ping(containers, agent_fingers)

        # delete agents that don't exist as containers
        for agent in agents:
            if agent not in containers:
                finger = agent_fingers[agent]
                de_register_agent(finger)

    except Exception as E:
        print "unable to sync containers or agents!: %s" % E


def main(argv):
    global API_KEY, CADVISOR, API_URL, EXCHANGE_URL

    try:
        opts, args = getopt.getopt(argv, "ha:c:u:e::", ["apikey=", "cadvisor=", "apiurl=", "exchangeurl="])
    except getopt.GetoptError:
        print 'discover.py -a <apikey> -c <cadvisor address:port> -u <dataloop api address:port> -e <dataloop exchange address:port>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'discover.py -a <apikey> -c <cadvisor address:port> -u <dataloop address:port> -e <dataloop exchange address:port>'
            sys.exit()
        elif opt in ("-a", "--apikey"):
            API_KEY = arg
        elif opt in ("-c", "--cadvisor"):
            CADVISOR = arg
        elif opt in ("-u", "--apiurl"):
            API_URL = arg
        elif opt in ("-e", "--exchangeurl"):
            EXCHANGE_URL = arg

    print 'apikey: ' + API_KEY
    print 'api url: ' + API_URL
    print 'exchange url: ' + EXCHANGE_URL
    print 'cadvisor endpoint: ' + CADVISOR
    print 'initial containers: ' + str(get_containers())
    print 'initial agents: ' + str(get_agents())

    print "Container Auto-Discovery running. Press ctrl+c to exit!"
    while True:

        sync()
        sleep(5)


if __name__ == "__main__":
    main(sys.argv[1:])
