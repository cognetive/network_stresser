## Test suite for Skydive

This folder holds specific Skydive test stress code 

### Prerequisites:
- Install python:
    ````
    > apt-get install python
    ````
- Install pip:
    ````
    > apt-get install pip
    ````
- Install bc:
    ````
    > apt-get install bc
    ````
- Install pyyaml:
    ````
    > pip install pyyaml
    ````
- Install and configure HELM:
    ````
    > HELM_GET=https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get
    > HELM_VER="v2.9.1"
    > curl $HELM_GET | sed 's/helm version/helm --debug version/' | bash -s -- --version $HELM_VER
    > helm init
    > helm repo add ibm-charts https://raw.githubusercontent.com/IBM/charts/master/repo/stable/
    ````

- Note 1: 
If you are running the stresser from a pod inside the k8s cluster, you should allow access to k8s from that pod.
In order to do that, execute:
    ````
    > kubectl create clusterrolebinding default-admin --clusterrole cluster-admin --serviceaccount=default:default
    ````

- Note 2: 
To monitor additional pods (for example- Skydive pods that are deployed in different namespace), you can add/change the configuration file: **"stats.conf"**. 
  - For example:
  To monitor also skydive pods under the 'monitoring' namespace, add to the file:
  **"monitoring app skydive-ibm-skydive-dev"**

### Usage:
- Execute from the CLI, under relative directory of: **"network_stresser/tests/skydive_tests/"**:
    ````
    > python run_iperf_tests.py
    ````
