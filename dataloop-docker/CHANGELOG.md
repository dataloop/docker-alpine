# Change Log

All noteable changes to this project will be documented in this file


---

## DEPRECATED

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
