# Change Log

All noteable changes to this project will be documented in this file

Version releases track the dataloop-agent semver  
The patch version is for the number of containers built at this release level

## 1.3.71-1 - 2017/05/25

* docker-worker: fix - handle kubernetes image format 
* docker-worker: new - put the services discovered in the agent tag
* docker-worker: fix - handle empty labels in swarm
* agent: fix - don't crash when docker top fail, carry on with empty proc list
* agent: fix - filter the outlyer container when the container was started with --net=host
* agent: fix - obtaining container ip address when docker container network doesnt exists 
* plugin-helper: fix - nginx plugin against containers
* plugin-helper: fix - postgress plugin against containers
* app: new - in the installer, discover docker pack for containers
* docker-alpine: big fix - updating our daemonset in kubernetes don't crash the whole cluster

## 1.3.52-2 - 2017/04/27

* only log stacktrace if debug flag is on


## 1.3.52-2 - 2017/04/26

* enabled load_1 metrics and added base.count. 
* added exception handling if one of the metric collection fail
* update the containers states when their host disconnect (and/or reconnect as well). If the host becomes orange/red its containers will become orange too instead of staying green in the UI.


## 1.3.49-1

* Filter out the agent container as it is considered the host

---
## 1.3.47-1

* fix IO logging error

---
## 1.3.46-1

* disable load collection

---
## 1.3.45-1

* Send host interface data to docker worker
* Send netstat output for each container
* Pass procfs directory to procfsutil

---
## 1.3.44-1

* return entire UUID for docker container
---


## DATALOOP\DATALOOP-DOCKER DEPRECATED

* ```dataloop\dataloop-docker` becomes `outlyer\agent`

---

Version releases are in the format:  

```
<Year>.<Month>-<build number this month>
```

---

## 2017.4-1

**Please Update the Base pack to 1.10+ to fix an issue with devicemapper mountpoints inside containers**

* kubernetes: fix label checking on filtering
* fix memory collection
* merged into agent base -metrics collection and discovery embedded in agent code


--- 

## 2017.03-1

**This release changes the base metrics paths. See the METRICS.md file for OS level base metrics returned by this container. Please update your Docker Pack**

* extend from dataloop\agent-base on Alpine Linux
* remove cadvisor
* collect metrics directly from cgroups files
* merge discovery, presence and tagging to one service
* improved logging and debug flag
* all logs go to `docker logs`
* example docker-compose file
* experimental Kubernetes Support
* kubernetes: don't sync paused and kube-system containers
* fix a bug where container processes were not grouped together
* improve container tagging
* send container metrics in batch
* metrics: fix rate calculation
* deregister all the synced container when dataloop-docker is stoped


---

## v1.3.19

* Line in the sand version number

---

## Prior releases

* Initial docker discovery and monitoring
* uses CAdvisor for metrics
* 
