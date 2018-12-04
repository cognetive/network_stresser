## Test suite for Skydive

This folder holds specific Skydive test stress code 

### Prerequisites:
- Install python:
    ````
    apt-get install -y python
    ````
- Install pip:
    ````
    apt-get install -y python-pip
    ````
- Install pyyaml:
    ````
    pip install pyyaml
    ````
- Install git:
    ````
    apt-get install -y git
    ````
- Install curl:
    ````
    apt-get install -y curl
    ````
- Install wget:
    ````
    apt-get install -y wget
    ````
- Install bc:
    ````
    apt-get install -y bc
    ````
- Install K8S:
    ````
    OS=linux
    ARCH=amd64
    TARGET_DIR=/usr/bin
    K8S_VERSION="v1.10.0"
    KUBECTL_URL="https://storage.googleapis.com/kubernetes-release/release/$K8S_VERSION/bin/$OS/$ARCH/kubectl"
    wget --no-check-certificate -O kubectl $KUBECTL_URL
    chmod a+x kubectl
    mv kubectl $TARGET_DIR/kubectl
    ````
- Install and configure HELM:
    ````
    HELM_GET=https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get
    HELM_VER="v2.9.1"
    curl $HELM_GET | sed 's/helm version/helm --debug version/' | bash -s -- --version $HELM_VER
    helm init
    helm repo add ibm-charts https://raw.githubusercontent.com/IBM/charts/master/repo/stable/
    ````
    
- To install Network stresser:
    ````
    cd ~
    git clone https://github.com/cognetive/network_stresser.git
    cd network_stresser/tests/skydive_tests
    ````

- Note 1: 
If you are running the stresser from a pod inside the k8s cluster, you should allow access to k8s from that pod.
In order to do that, execute from the host side where you can enter this pod (not from the pod itself):
    ````
    kubectl create clusterrolebinding default-admin --clusterrole cluster-admin --serviceaccount=default:default
    ````

- Note 2: 
To monitor additional pods (for example- Skydive pods that are deployed in different namespace), you can add/change the configuration file: **"stats.conf"**. 
  - For example:
  To monitor also skydive pods under the 'monitoring' namespace, add to the file:
  **"monitoring app skydive-ibm-skydive-dev"**

### Usage:
- Execute from the CLI, under relative directory of: **"network_stresser/tests/skydive_tests/"**:
    ````
    python run_tests.py
    ````

- Note 1: 
To configure execution of tests, modify the file tests_conf.yaml and rerun. Full list of configration parameters can be found in  tests_conf_template.yaml

- Note 2:
The test mode can be ingress, wherein the receivers are started inside the local cluster together with skydive and the generators reside in some external cluster; egress where the generators and skydive are inside and the receivers are in some other cluster; and finally "internal".
	- If you know the external IP and you with to enter it so that it would be used automatically, change the valuse of the field in tests_conf.yaml and set it to that IP. Otherwise, if you'd like the test system to automatically extract this IP using the script get_target_ip.sh, set the value to "auto".
	- Changing the above parameters suffices to generate the desired tests.

- None 3:
To run the tests in either "egress" or "ingress" mode:
    1 - Create two new directories: "internal_export_dir" and "external_export_dir" in network_stresser's parent folder.  The two directories should include scripts that provide essential information regarding each of the external and local clusters.

    2 - Each of the two directories must contain two shell scripts: get_target_ip which returns an ip of some node in the cluster and connect_to_cluster.sh which returns the an export line.
 

