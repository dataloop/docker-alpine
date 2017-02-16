import logging
import requests
import grequests

logger = logging.getLogger('API')

API_TIMEOUT = 5


def list_agents(ctx, mac):
    '''list agents with the same mac address'''

    url = "%s/agents?mac=%s" % (ctx['api_host'], mac)
    headers = _get_request_headers(ctx)
    try:
        resp = requests.get(url, headers=headers, timeout=API_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except:
        logger.warn(url, "| request failed")


def deregister_agents(ctx, agent_ids):
    api_host = ctx['api_host']
    headers = _get_request_headers(ctx)

    def create_request(id):
        url = "%s/agents/%s/deregister" % (api_host, id)
        return grequests.post(url, headers=headers, timeout=API_TIMEOUT)

    reqs = map(create_request, agent_ids)
    grequests.map(reqs, exception_handler=_grequest_exception_handler)


def tag_agents(ctx, agents):
    '''update agent tags, will completely replace previous ones'''

    api_host = ctx['api_host']
    headers = _get_request_headers(ctx)

    def create_request(agent):
        url = "%s/agents/%s/tags" % (api_host, agent['finger'])
        return grequests.put(url, json=agent, headers=headers)

    reqs = map(create_request, agents)
    grequests.map(reqs, exception_handler=_grequest_exception_handler)


def ping_agents(ctx, agents):
    '''send a ping to the exchange, will also register agents if they arent already'''

    api_host = ctx['api_host']
    headers = _get_request_headers(ctx)

    def create_request(agent):
        url = "%s/agents/%s/ping" % (api_host, agent['finger'])
        return grequests.post(url, json=agent, headers=headers, timeout=API_TIMEOUT)

    reqs = map(create_request, agents)
    grequests.map(reqs, exception_handler=_grequest_exception_handler)


def _get_request_headers(ctx):
    return {
        "Content-type": "application/json",
        "Authorization": "Bearer " + ctx['api_key']
    }

def _grequest_exception_handler(request, exception):
    logger.warn(request.url, "| request failed")
