# odf-deployment

# configure the configure.yaml 

worker_nodes: list of worker nodes in cluster   
e.g.
```
worker_nodes:
  - compute-0
  - compute-1
  - compute-2
``` 
platform: the platform of cluster e.g. ['ibm', 'aws' , 'vsphere']   
odf_version: od version e.g. 'quay.io/rhceph-dev/ocs-registry:latest-stable-4.15'  
odf_channel: odf channel e.g. 'stable-4.15' 

# Running the script:
```
python install_odf.py
```
