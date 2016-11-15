#!/usr/bin/env python

import requests

req = requests.get('http://localhost:9104/metrics')
print(req.text)
